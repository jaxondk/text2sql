from fastapi import APIRouter

from app.api.endpoints import queries, databases, llms

api_router = APIRouter()

api_router.include_router(queries.router, prefix="/queries", tags=["queries"])
api_router.include_router(databases.router, prefix="/databases", tags=["databases"])
api_router.include_router(llms.router, prefix="/llms", tags=["llms"]) 