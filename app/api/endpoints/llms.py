from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

from app.llm.manager import LLMManager
from app.core.state import app_state

router = APIRouter()


class LLMInfo(BaseModel):
    id: str
    name: str
    provider: str
    model: str
    description: Optional[str] = None
    config: Dict[str, Any] = {}


class LLMConfigRequest(BaseModel):
    name: str
    provider: str
    model: str
    description: Optional[str] = None
    api_key: Optional[str] = None
    config: Dict[str, Any] = {}


@router.get("/", response_model=List[LLMInfo])
async def list_llms():
    """
    List all available LLM configurations
    """
    try:
        llm_manager = LLMManager()
        llms = await llm_manager.list_llms()
        return llms
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=LLMInfo)
async def add_llm(request: LLMConfigRequest):
    """
    Add a new LLM configuration
    """
    try:
        llm_manager = LLMManager()
        llm_id = await llm_manager.add_llm(
            name=request.name,
            provider=request.provider,
            model=request.model,
            description=request.description,
            api_key=request.api_key,
            config=request.config,
        )

        return {
            "id": llm_id,
            "name": request.name,
            "provider": request.provider,
            "model": request.model,
            "description": request.description,
            "config": request.config,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers", response_model=List[str])
async def list_providers():
    """
    List all available LLM providers
    """
    try:
        llm_manager = LLMManager()
        providers = await llm_manager.list_providers()
        return providers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{llm_id}")
async def remove_llm(llm_id: str):
    """
    Remove an LLM configuration
    """
    try:
        llm_manager = LLMManager()
        success = await llm_manager.remove_llm(llm_id)
        if not success:
            raise HTTPException(status_code=404, detail="LLM not found")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_app_status():
    """
    Get the application loading status
    """
    return {"status": app_state}
