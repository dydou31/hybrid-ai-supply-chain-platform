from app.database import SessionLocal
from app.ai.models import KnowledgeDocument
from app.ai.chunk_models import KnowledgeChunk
from app.ai.embeddings import generate_embedding
from app.ai.chunking import chunk_text


def ingest_document(title: str, content: str, source: str | None = None):
    db = SessionLocal()

    try:
        chunks = chunk_text(content)

        if not chunks:
            raise ValueError("Cannot ingest an empty document.")

        document = KnowledgeDocument(
            title=title,
            content=content,
            source=source,
            embedding=generate_embedding(chunks[0]),
        )

        db.add(document)
        db.flush()

        for index, chunk_content in enumerate(chunks):
            chunk = KnowledgeChunk(
                document_id=document.id,
                chunk_index=index,
                content=chunk_content,
                embedding=generate_embedding(chunk_content),
            )
            db.add(chunk)

        db.commit()
        db.refresh(document)

        return document

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()
