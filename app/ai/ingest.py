from app.database import SessionLocal
from app.ai.models import KnowledgeDocument
from app.ai.embeddings import generate_embedding


def ingest_document(title: str, content: str, source: str | None = None):
    db = SessionLocal()

    try:
        document = KnowledgeDocument(
            title=title,
            content=content,
            source=source,
            embedding=generate_embedding(content),
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document
    finally:
        db.close()
