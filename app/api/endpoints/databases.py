from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

from app.db.manager import DatabaseManager
from app.core.models import DatabaseInfo, TableSchema

router = APIRouter()

class DatabaseConnectionRequest(BaseModel):
    name: str
    type: str = "postgres"
    connection_string: str
    description: Optional[str] = None

class DatabaseConnectionResponse(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    connected: bool

@router.post("/", response_model=DatabaseConnectionResponse)
async def add_database(request: DatabaseConnectionRequest):
    """
    Add a new database connection
    """
    try:
        db_manager = DatabaseManager()
        db_id = await db_manager.add_database(
            name=request.name,
            db_type=request.type,
            connection_string=request.connection_string,
            description=request.description
        )
        
        return {
            "id": db_id,
            "name": request.name,
            "type": request.type,
            "description": request.description,
            "connected": True
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[DatabaseConnectionResponse])
async def list_databases():
    """
    List all database connections
    """
    try:
        db_manager = DatabaseManager()
        databases = await db_manager.list_databases()
        return databases
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{db_id}", response_model=DatabaseInfo)
async def get_database(db_id: str):
    """
    Get database information
    """
    try:
        db_manager = DatabaseManager()
        db_info = await db_manager.get_database_info(db_id)
        if not db_info:
            raise HTTPException(status_code=404, detail="Database not found")
        return db_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{db_id}/tables", response_model=List[TableSchema])
async def get_tables(db_id: str):
    """
    Get tables in a database
    """
    try:
        db_manager = DatabaseManager()
        tables = await db_manager.get_tables(db_id)
        return tables
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{db_id}")
async def remove_database(db_id: str):
    """
    Remove a database connection
    """
    try:
        db_manager = DatabaseManager()
        success = await db_manager.remove_database(db_id)
        if not success:
            raise HTTPException(status_code=404, detail="Database not found")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 