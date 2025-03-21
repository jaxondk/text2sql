import os
import json
import logging
from typing import List, Dict, Any, Optional
import numpy as np

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

from app.core.models import TableSchema

logger = logging.getLogger(__name__)

class VectorStore:
    def __init__(self):
        self.vector_db_path = os.getenv("VECTOR_DB_PATH", "./data/vectordb")
        self.vector_db_type = os.getenv("VECTOR_DB_TYPE", "chroma")
        self.embedding_model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # Ensure vector db directory exists
        os.makedirs(self.vector_db_path, exist_ok=True)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(self.embedding_model_name)
        
        # Initialize vector db
        self.client = chromadb.PersistentClient(path=self.vector_db_path)
        
        # Create or get collection for table schemas
        self.collection = self.client.get_or_create_collection(
            name="table_schemas",
            metadata={"hnsw:space": "cosine"}
        )
    
    async def index_tables(self, database_id: str, tables: List[TableSchema]):
        """
        Index table schemas in vector store
        """
        try:
            # Delete existing entries for this database
            await self.remove_tables(database_id)
            
            # Prepare documents, embeddings, and metadata
            documents = []
            metadatas = []
            ids = []
            
            for table in tables:
                # Convert table to string for embedding
                table_str = self._table_to_string(table)
                
                # Add to document list
                documents.append(table_str)
                
                # Add metadata
                metadatas.append({
                    "database_id": database_id,
                    "table_name": table.name,
                    "schema": table.json()
                })
                
                # Create ID
                ids.append(f"{database_id}_{table.name}")
            
            # Add to vector store
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            
            return True
        except Exception as e:
            logger.error(f"Error indexing tables: {str(e)}")
            raise
    
    async def search_tables(
        self,
        query: str,
        database_id: str,
        limit: int = 5
    ) -> List[TableSchema]:
        """
        Search for relevant tables using vector search
        """
        try:
            # Search in vector store
            results = self.collection.query(
                query_texts=[query],
                where={"database_id": database_id},
                n_results=limit
            )
            
            # Extract table schemas from results
            tables = []
            if results and results["metadatas"]:
                for metadata in results["metadatas"][0]:
                    # Parse schema JSON
                    schema_json = metadata.get("schema")
                    if schema_json:
                        if isinstance(schema_json, str):
                            schema_dict = json.loads(schema_json)
                        else:
                            schema_dict = schema_json
                        
                        # Create TableSchema object
                        table = TableSchema.parse_obj(schema_dict)
                        tables.append(table)
            
            return tables
        except Exception as e:
            logger.error(f"Error searching tables: {str(e)}")
            return []
    
    async def remove_tables(self, database_id: str):
        """
        Remove table schemas for a database
        """
        try:
            self.collection.delete(
                where={"database_id": database_id}
            )
            return True
        except Exception as e:
            logger.error(f"Error removing tables: {str(e)}")
            return False
    
    def _table_to_string(self, table: TableSchema) -> str:
        """
        Convert TableSchema to string for embedding
        """
        result = f"Table: {table.name}\n"
        
        if table.description:
            result += f"Description: {table.description}\n"
        
        result += "Columns:\n"
        
        for column in table.columns:
            col_str = f"- {column.name}: {column.data_type}"
            
            if column.description:
                col_str += f" - {column.description}"
            
            if column.is_primary_key:
                col_str += " (Primary Key)"
            
            if column.is_foreign_key and column.references:
                col_str += f" (Foreign Key to {column.references})"
            
            result += col_str + "\n"
        
        return result 