from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.service import ask_rag
from app.ai.models import KnowledgeDocument
from app.database import get_db

router = APIRouter(prefix="/ai", tags=["AI"])


class AskRequest(BaseModel):
    question: str


@router.post("/ask")
def ask(request: AskRequest):
    return ask_rag(request.question)


@router.get("/knowledge/count")
def knowledge_count(db: Session = Depends(get_db)):
    count = db.query(KnowledgeDocument).count()
    return {"count": count}
