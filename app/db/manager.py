import os
import json
import uuid
import logging
from typing import List, Dict, Any, Optional

from app.db.adapters import get_db_adapter
from app.core.models import DatabaseInfo, TableSchema
from app.utils.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self):
        self.config_dir = os.path.join(os.getcwd(), "data", "config")
        self.db_config_file = os.path.join(self.config_dir, "databases.json")
        self.vector_store = None

        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)

        # Create config file if it doesn't exist
        if not os.path.exists(self.db_config_file):
            with open(self.db_config_file, "w") as f:
                json.dump([], f)

        # We'll initialize the vector store lazily to handle potential errors

    async def _init_vector_store(self):
        """Initialize vector store if it hasn't been initialized yet"""
        if self.vector_store is None:
            try:
                self.vector_store = get_vector_store()
                return True
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {str(e)}")
                return False
        return True

    async def add_database(
        self,
        name: str,
        db_type: str,
        connection_string: str,
        description: Optional[str] = None,
    ) -> str:
        """
        Add a new database connection
        """
        # Validate connection
        adapter = get_db_adapter(db_type, connection_string)
        await adapter.test_connection()

        # Generate ID
        db_id = str(uuid.uuid4())

        # Load existing configs
        configs = self._load_configs()

        # Add new config
        configs.append(
            {
                "id": db_id,
                "name": name,
                "type": db_type,
                "connection_string": connection_string,
                "description": description,
            }
        )

        # Save configs
        self._save_configs(configs)

        # Load and index table schemas
        try:
            schemas = await adapter.get_table_schemas()

            # Initialize vector store if possible
            if await self._init_vector_store() and self.vector_store:
                try:
                    await self.vector_store.index_tables(db_id, schemas)
                except Exception as e:
                    logger.error(f"Error indexing schemas: {str(e)}")
        except Exception as e:
            logger.error(f"Error getting schemas: {str(e)}")

        return db_id

    async def list_databases(self) -> List[Dict[str, Any]]:
        """
        List all database connections
        """
        configs = self._load_configs()
        return [
            {
                "id": config["id"],
                "name": config["name"],
                "type": config["type"],
                "description": config.get("description"),
                "connected": True,  # In a real implementation, we would test the connection
            }
            for config in configs
        ]

    async def get_database_info(self, db_id: str) -> Optional[DatabaseInfo]:
        """
        Get database information including table schemas
        """
        # Find config
        config = self._get_config_by_id(db_id)
        if not config:
            return None

        # Get schemas
        try:
            adapter = get_db_adapter(config["type"], config["connection_string"])
            schemas = await adapter.get_table_schemas()

            return DatabaseInfo(
                id=db_id,
                name=config["name"],
                type=config["type"],
                description=config.get("description"),
                tables=schemas,
            )
        except Exception as e:
            logger.error(f"Error getting database info: {str(e)}")
            return None

    async def get_tables(self, db_id: str) -> List[TableSchema]:
        """
        Get tables in a database
        """
        # Find config
        config = self._get_config_by_id(db_id)
        if not config:
            return []

        # Get schemas
        try:
            adapter = get_db_adapter(config["type"], config["connection_string"])
            return await adapter.get_table_schemas()
        except Exception as e:
            logger.error(f"Error getting tables: {str(e)}")
            return []

    async def remove_database(self, db_id: str) -> bool:
        """
        Remove a database connection
        """
        configs = self._load_configs()

        # Find config by ID
        for i, config in enumerate(configs):
            if config["id"] == db_id:
                # Remove from configs
                configs.pop(i)
                self._save_configs(configs)

                # Remove from vector store
                if await self._init_vector_store() and self.vector_store:
                    try:
                        await self.vector_store.remove_tables(db_id)
                    except Exception as e:
                        logger.error(
                            f"Error removing tables from vector store: {str(e)}"
                        )

                return True

        return False

    async def initialize_default_database(self) -> Optional[str]:
        """
        Initialize a default database connection if none exists
        """
        configs = self._load_configs()
        if configs:
            logger.info("Database connections already exist")

            # Get the first database connection and index its tables
            db_id = configs[0]["id"]
            logger.info(f"Reindexing tables for database {db_id}")

            try:
                # Get the database adapter
                config = self._get_config_by_id(db_id)
                if not config:
                    logger.error(f"Database config not found for ID: {db_id}")
                    return db_id

                # Get the adapter
                adapter = get_db_adapter(config["type"], config["connection_string"])

                # Get the schemas
                logger.info("Getting table schemas...")
                schemas = await adapter.get_table_schemas()
                logger.info(f"Found {len(schemas)} tables")

                # Index the schemas
                if await self._init_vector_store() and self.vector_store:
                    logger.info("Indexing tables in vector store...")
                    await self.vector_store.index_tables(db_id, schemas)
                    logger.info("Tables indexed successfully")
            except Exception as e:
                logger.error(f"Error reindexing tables: {str(e)}")

            return db_id

        logger.info("No database connections found, initializing default connection")

        # Get connection details from environment variables
        default_connection_string = os.getenv(
            "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"
        )
        default_db_type = os.getenv("DATABASE_TYPE", "postgres")

        try:
            db_id = await self.add_database(
                name="Default Database",
                db_type=default_db_type,
                connection_string=default_connection_string,
                description="Default database connection initialized from environment variables",
            )
            logger.info(
                f"Successfully initialized default database connection with ID: {db_id}"
            )
            return db_id
        except Exception as e:
            logger.error(f"Failed to initialize default database connection: {str(e)}")
            return None

    def get_connection_string(self, db_id: str) -> Optional[str]:
        """
        Get connection string for a database
        """
        config = self._get_config_by_id(db_id)
        return config["connection_string"] if config else None

    def get_db_type(self, db_id: str) -> Optional[str]:
        """
        Get database type for a database
        """
        config = self._get_config_by_id(db_id)
        return config["type"] if config else None

    def _load_configs(self) -> List[Dict[str, Any]]:
        """
        Load database configurations from file
        """
        try:
            with open(self.db_config_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading database configs: {str(e)}")
            return []

    def _save_configs(self, configs: List[Dict[str, Any]]):
        """
        Save database configurations to file
        """
        try:
            with open(self.db_config_file, "w") as f:
                json.dump(configs, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving database configs: {str(e)}")

    def _get_config_by_id(self, db_id: str) -> Optional[Dict[str, Any]]:
        """
        Get database configuration by ID
        """
        configs = self._load_configs()
        for config in configs:
            if config["id"] == db_id:
                return config
        return None
