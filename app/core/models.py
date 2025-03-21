from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union

class ColumnInfo(BaseModel):
    name: str
    data_type: str
    description: Optional[str] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    references: Optional[str] = None

class TableSchema(BaseModel):
    name: str
    description: Optional[str] = None
    columns: List[ColumnInfo]

class DatabaseInfo(BaseModel):
    id: str
    name: str
    type: str
    description: Optional[str] = None
    tables: List[TableSchema] = []

class TraceData(BaseModel):
    reasoning: str = ""
    retrieved_schemas: List[TableSchema] = []
    generated_sql: str = ""
    execution_result: Optional[Any] = None
    errors: List[str] = []
    attempts: int = 1

class QueryResult(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    row_count: int

class QueryResponse(BaseModel):
    query: str
    sql: str
    result: Optional[QueryResult] = None
    database_id: Optional[str] = None
    llm_provider: str
    trace: TraceData
    error: Optional[str] = None
    success: bool 