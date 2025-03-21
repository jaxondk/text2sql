import logging
from typing import List, Dict, Any, Optional
import sqlalchemy
from sqlalchemy import create_engine, MetaData, Table, Column, inspect
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from abc import ABC, abstractmethod

from app.core.models import TableSchema, ColumnInfo

logger = logging.getLogger(__name__)


class DBAdapter(ABC):
    """Base database adapter class"""

    def __init__(self, connection_string: str):
        self.connection_string = connection_string

    @abstractmethod
    async def test_connection(self) -> bool:
        """Test database connection"""
        pass

    @abstractmethod
    async def get_table_schemas(self) -> List[TableSchema]:
        """Get table schemas from database"""
        pass

    @abstractmethod
    async def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query"""
        pass


class PostgresAdapter(DBAdapter):
    """PostgreSQL database adapter"""

    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        # Convert connection string to async version if needed
        if not connection_string.startswith("postgresql+asyncpg://"):
            if connection_string.startswith("postgresql://"):
                self.connection_string = connection_string.replace(
                    "postgresql://", "postgresql+asyncpg://"
                )
            else:
                self.connection_string = f"postgresql+asyncpg://{connection_string}"
        else:
            self.connection_string = connection_string

        self.engine = create_async_engine(self.connection_string)

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(sqlalchemy.text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {str(e)}")
            raise ValueError(f"Failed to connect to PostgreSQL: {str(e)}")

    async def get_table_schemas(self) -> List[TableSchema]:
        """Get table schemas from PostgreSQL database"""
        try:
            metadata = MetaData()
            async with self.engine.connect() as conn:
                await conn.run_sync(metadata.reflect)

                schemas = []

                for table_name in metadata.tables:
                    table = metadata.tables[table_name]

                    # Get primary keys
                    pk_constraint = table.primary_key
                    pk_columns = {c.name for c in pk_constraint.columns}

                    # Get foreign keys
                    fk_info = {}
                    for fk in table.foreign_keys:
                        fk_info[fk.parent.name] = fk.target_fullname

                    columns = []
                    for column in table.columns:
                        columns.append(
                            ColumnInfo(
                                name=column.name,
                                data_type=str(column.type),
                                is_primary_key=column.name in pk_columns,
                                is_foreign_key=column.name in fk_info,
                                references=fk_info.get(column.name),
                            )
                        )

                    schemas.append(TableSchema(name=table_name, columns=columns))

                return schemas
        except Exception as e:
            logger.error(f"Error getting table schemas: {str(e)}")
            raise ValueError(f"Failed to get table schemas: {str(e)}")

    async def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query on PostgreSQL database"""
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(sqlalchemy.text(sql))
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    return {
                        "columns": list(columns),
                        "rows": [list(row) for row in rows],
                    }
                return {"columns": [], "rows": []}
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise ValueError(f"Failed to execute query: {str(e)}")


class MySQLAdapter(DBAdapter):
    """MySQL database adapter"""

    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        # Convert connection string to async version if needed
        if not connection_string.startswith("mysql+aiomysql://"):
            if connection_string.startswith("mysql://"):
                self.connection_string = connection_string.replace(
                    "mysql://", "mysql+aiomysql://"
                )
            else:
                self.connection_string = f"mysql+aiomysql://{connection_string}"
        else:
            self.connection_string = connection_string

        self.engine = create_async_engine(self.connection_string)

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(sqlalchemy.text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Error connecting to MySQL: {str(e)}")
            raise ValueError(f"Failed to connect to MySQL: {str(e)}")

    async def get_table_schemas(self) -> List[TableSchema]:
        """Get table schemas from MySQL database"""
        try:
            metadata = MetaData()
            async with self.engine.connect() as conn:
                await conn.run_sync(metadata.reflect)

                schemas = []

                for table_name in metadata.tables:
                    table = metadata.tables[table_name]

                    # Get primary keys
                    pk_constraint = table.primary_key
                    pk_columns = {c.name for c in pk_constraint.columns}

                    # Get foreign keys
                    fk_info = {}
                    for fk in table.foreign_keys:
                        fk_info[fk.parent.name] = fk.target_fullname

                    columns = []
                    for column in table.columns:
                        columns.append(
                            ColumnInfo(
                                name=column.name,
                                data_type=str(column.type),
                                is_primary_key=column.name in pk_columns,
                                is_foreign_key=column.name in fk_info,
                                references=fk_info.get(column.name),
                            )
                        )

                    schemas.append(TableSchema(name=table_name, columns=columns))

                return schemas
        except Exception as e:
            logger.error(f"Error getting table schemas: {str(e)}")
            raise ValueError(f"Failed to get table schemas: {str(e)}")

    async def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query on MySQL database"""
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(sqlalchemy.text(sql))
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    return {
                        "columns": list(columns),
                        "rows": [list(row) for row in rows],
                    }
                return {"columns": [], "rows": []}
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise ValueError(f"Failed to execute query: {str(e)}")


class SQLiteAdapter(DBAdapter):
    """SQLite database adapter"""

    def __init__(self, connection_string: str):
        super().__init__(connection_string)
        # Convert connection string to async version if needed
        if not connection_string.startswith("sqlite+aiosqlite://"):
            if connection_string.startswith("sqlite://"):
                self.connection_string = connection_string.replace(
                    "sqlite://", "sqlite+aiosqlite://"
                )
            else:
                self.connection_string = f"sqlite+aiosqlite:///{connection_string}"
        else:
            self.connection_string = connection_string

        self.engine = create_async_engine(self.connection_string)

    async def test_connection(self) -> bool:
        """Test database connection"""
        try:
            async with self.engine.connect() as conn:
                await conn.execute(sqlalchemy.text("SELECT 1"))
            return True
        except Exception as e:
            logger.error(f"Error connecting to SQLite: {str(e)}")
            raise ValueError(f"Failed to connect to SQLite: {str(e)}")

    async def get_table_schemas(self) -> List[TableSchema]:
        """Get table schemas from SQLite database"""
        try:
            metadata = MetaData()
            async with self.engine.connect() as conn:
                await conn.run_sync(metadata.reflect)

                schemas = []

                for table_name in metadata.tables:
                    table = metadata.tables[table_name]

                    # Get primary keys
                    pk_constraint = table.primary_key
                    pk_columns = {c.name for c in pk_constraint.columns}

                    # Get foreign keys
                    fk_info = {}
                    for fk in table.foreign_keys:
                        fk_info[fk.parent.name] = fk.target_fullname

                    columns = []
                    for column in table.columns:
                        columns.append(
                            ColumnInfo(
                                name=column.name,
                                data_type=str(column.type),
                                is_primary_key=column.name in pk_columns,
                                is_foreign_key=column.name in fk_info,
                                references=fk_info.get(column.name),
                            )
                        )

                    schemas.append(TableSchema(name=table_name, columns=columns))

                return schemas
        except Exception as e:
            logger.error(f"Error getting table schemas: {str(e)}")
            raise ValueError(f"Failed to get table schemas: {str(e)}")

    async def execute_query(self, sql: str) -> Dict[str, Any]:
        """Execute SQL query on SQLite database"""
        try:
            async with self.engine.connect() as conn:
                result = await conn.execute(sqlalchemy.text(sql))
                if result.returns_rows:
                    rows = result.fetchall()
                    columns = result.keys()
                    return {
                        "columns": list(columns),
                        "rows": [list(row) for row in rows],
                    }
                return {"columns": [], "rows": []}
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            raise ValueError(f"Failed to execute query: {str(e)}")


def get_db_adapter(db_type: str, connection_string: str) -> DBAdapter:
    """
    Get database adapter based on database type
    """
    if db_type.lower() == "postgres" or db_type.lower() == "postgresql":
        return PostgresAdapter(connection_string)
    elif db_type.lower() == "mysql":
        return MySQLAdapter(connection_string)
    elif db_type.lower() == "sqlite":
        return SQLiteAdapter(connection_string)
    else:
        raise ValueError(f"Unsupported database type: {db_type}")
