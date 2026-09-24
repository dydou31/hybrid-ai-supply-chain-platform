from fastapi import APIRouter
from pydantic import BaseModel

from app.ai.service import ask_rag

router = APIRouter(prefix="/ai", tags=["AI"])


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask(request: AskRequest):
    return ask_rag(request.question)
