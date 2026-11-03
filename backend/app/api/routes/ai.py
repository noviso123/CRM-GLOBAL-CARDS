from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.agents.agent_manager import AgentManager
from app.api.dependencies import get_current_user, get_dbf_manager
from app.database.dbf_manager import DBFManager

router = APIRouter(prefix="/api/ai", tags=["Inteligência Artificial"])


class AIChatRequest(BaseModel):
    prompt: str
    client_id: Optional[str] = None


@router.post("/chat")
def ai_chat(
    payload: AIChatRequest,
    user: Dict[str, Any] = Depends(get_current_user),
    mgr: DBFManager = Depends(get_dbf_manager),
) -> Dict[str, Any]:
    agent = AgentManager(mgr, user)
    return agent.process_prompt(payload.prompt, client_id=payload.client_id)

