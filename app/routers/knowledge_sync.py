from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ai.models import KnowledgeDocument
from app.ai.chunk_models import KnowledgeChunk
from app.routers.knowledge_sync_schemas import KnowledgeSyncPayload
from app.routers.sync_auth import verify_sync_key


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(verify_sync_key)],
)


@router.post("/sync/knowledge")
def sync_knowledge(
    payload: KnowledgeSyncPayload,
    db: Session = Depends(get_db),
):
    results = []
    seen_sources = set()

    # Refuser les sources dupliquées dans une même requête.
    for item in payload.documents:
        if item.source in seen_sources:
            raise HTTPException(
                status_code=422,
                detail=f"Duplicate source: {item.source}",
            )
        seen_sources.add(item.source)

        indexes = [chunk.chunk_index for chunk in item.chunks]
        if len(indexes) != len(set(indexes)):
            raise HTTPException(
                status_code=422,
                detail=f"Duplicate chunk indexes: {item.source}",
            )

    for item in payload.documents:
        existing = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.source == item.source)
            .first()
        )

        # Détecter les documents ayant le même titre
        # mais une source différente.
        title_match = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.title == item.title)
            .first()
        )

        if title_match and title_match.source != item.source:
            results.append({
                "source": item.source,
                "action": "conflict",
                "reason": "Same title with a different source",
                "chunks": len(item.chunks),
            })
            continue

        action = "update" if existing else "create"

        if payload.dry_run:
            results.append({
                "source": item.source,
                "action": action,
                "chunks": len(item.chunks),
            })
            continue

        try:
            if existing:
                document = existing
                document.title = item.title
                document.content = item.content
                document.embedding = item.embedding

                db.query(KnowledgeChunk).filter(
                    KnowledgeChunk.document_id == document.id
                ).delete(synchronize_session=False)
            else:
                document = KnowledgeDocument(
                    title=item.title,
                    source=item.source,
                    content=item.content,
                    embedding=item.embedding,
                )
                db.add(document)
                db.flush()

            for chunk in item.chunks:
                db.add(KnowledgeChunk(
                    document_id=document.id,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    embedding=chunk.embedding,
                ))

            db.commit()

            results.append({
                "source": item.source,
                "action": action,
                "chunks": len(item.chunks),
            })

        except Exception:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Synchronization failed for {item.source}",
            )

    return {
        "dry_run": payload.dry_run,
        "documents_processed": len(results),
        "results": results,
    }
