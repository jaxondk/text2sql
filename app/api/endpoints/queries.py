from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any

from app.core.text2sql import Text2SQLProcessor
from app.core.models import QueryResponse, TraceData

router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    llm_provider: Optional[str] = None
    should_execute_sql: bool = True
    database_id: Optional[str] = None


@router.post("/", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """
    Process a natural language query and convert it to SQL
    """
    try:
        processor = Text2SQLProcessor(
            llm_provider=request.llm_provider, database_id=request.database_id
        )

        result = await processor.process(
            query=request.query, should_execute_sql=request.should_execute_sql
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=List[QueryResponse])
async def get_query_history():
    """
    Get query history
    """
    # This would fetch from a database in a real implementation
    return []
