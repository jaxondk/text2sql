import os
import logging
from typing import List, Dict, Any, Optional

from app.db.manager import DatabaseManager
from app.llm.manager import LLMManager
from app.core.models import QueryResponse, TraceData, TableSchema, QueryResult
from app.utils.db_utils import execute_sql

logger = logging.getLogger(__name__)


class Text2SQLProcessor:
    def __init__(
        self, llm_provider: Optional[str] = None, database_id: Optional[str] = None
    ):
        self.llm_provider = llm_provider or os.getenv("DEFAULT_LLM_PROVIDER", "openai")
        self.database_id = database_id
        self.db_manager = DatabaseManager()
        self.llm_manager = LLMManager()
        self.vector_store = None

    async def _init_vector_store(self):
        """Initialize vector store if it hasn't been initialized yet"""
        if self.vector_store is None:
            try:
                from app.utils.vector_store import VectorStore

                self.vector_store = VectorStore()
                return True
            except Exception as e:
                logger.error(f"Failed to initialize vector store: {str(e)}")
                return False
        return True

    async def process(
        self, query: str, should_execute_sql: bool = True
    ) -> QueryResponse:
        """
        Process a natural language query and convert it to SQL
        """
        trace = TraceData()

        try:
            # Get LLM
            llm = await self.llm_manager.get_llm(self.llm_provider)

            # Get database connection
            if not self.database_id:
                # Use the first available database if none specified
                databases = await self.db_manager.list_databases()
                if not databases:
                    raise ValueError("No database connections available")
                self.database_id = databases[0]["id"]

            # Get database info
            db_info = await self.db_manager.get_database_info(self.database_id)
            if not db_info:
                raise ValueError(f"Database with ID {self.database_id} not found")

            # Get table schemas directly from db_info if vector store fails
            relevant_tables = db_info.tables

            # Try to use vector store for semantic search if available
            if await self._init_vector_store() and self.vector_store:
                try:
                    semantic_tables = await self.vector_store.search_tables(
                        query=query, database_id=self.database_id
                    )
                    if semantic_tables:
                        relevant_tables = semantic_tables
                except Exception as e:
                    logger.error(
                        f"Error using vector search, falling back to all tables: {str(e)}"
                    )

            trace.retrieved_schemas = relevant_tables

            # Generate SQL using LLM
            reasoning, sql = await llm.generate_sql(query=query, tables=relevant_tables)
            trace.reasoning = reasoning
            trace.generated_sql = sql

            # Execute SQL if requested
            result = None
            error = None
            success = True

            if should_execute_sql:
                try:
                    result_data = await execute_sql(
                        sql=sql,
                        database_id=self.database_id,
                        db_manager=self.db_manager,
                    )

                    trace.execution_result = result_data

                    if result_data:
                        result = QueryResult(
                            columns=result_data["columns"],
                            rows=result_data["rows"],
                            row_count=len(result_data["rows"]),
                        )
                except Exception as e:
                    logger.error(f"Error executing SQL: {str(e)}")
                    trace.errors.append(str(e))
                    error = str(e)
                    success = False

                    # Retry with error feedback
                    if trace.attempts < 3:
                        trace.attempts += 1
                        retry_reasoning, retry_sql = await llm.generate_sql(
                            query=query,
                            tables=relevant_tables,
                            error=str(e),
                            previous_sql=sql,
                        )

                        trace.reasoning += (
                            f"\n\nRetry attempt {trace.attempts}:\n{retry_reasoning}"
                        )
                        trace.generated_sql = retry_sql

                        try:
                            result_data = await execute_sql(
                                sql=retry_sql,
                                database_id=self.database_id,
                                db_manager=self.db_manager,
                            )

                            trace.execution_result = result_data
                            sql = retry_sql  # Update SQL to the corrected version
                            error = None
                            success = True

                            if result_data:
                                result = QueryResult(
                                    columns=result_data["columns"],
                                    rows=result_data["rows"],
                                    row_count=len(result_data["rows"]),
                                )
                        except Exception as retry_e:
                            logger.error(f"Error executing SQL (retry): {str(retry_e)}")
                            trace.errors.append(str(retry_e))
                            error = str(retry_e)
                            success = False

            return QueryResponse(
                query=query,
                sql=sql,
                result=result,
                database_id=self.database_id,
                llm_provider=self.llm_provider,
                trace=trace,
                error=error,
                success=success,
            )

        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            return QueryResponse(
                query=query,
                sql="",
                result=None,
                database_id=self.database_id,
                llm_provider=self.llm_provider,
                trace=trace,
                error=str(e),
                success=False,
            )
