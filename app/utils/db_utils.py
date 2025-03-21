import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

async def execute_sql(sql: str, database_id: str, db_manager) -> Optional[Dict[str, Any]]:
    """
    Execute SQL query on a database
    """
    try:
        # Get database type and connection string
        db_type = db_manager.get_db_type(database_id)
        connection_string = db_manager.get_connection_string(database_id)
        
        if not db_type or not connection_string:
            raise ValueError(f"Database with ID {database_id} not found")
        
        # Get adapter
        from app.db.adapters import get_db_adapter
        adapter = get_db_adapter(db_type, connection_string)
        
        # Execute query
        result = await adapter.execute_query(sql)
        return result
    except Exception as e:
        logger.error(f"Error executing SQL: {str(e)}")
        raise 