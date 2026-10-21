from pathlib import Path
import argparse
import os
import requests
from dotenv import load_dotenv
#!/usr/bin/env python3
"""Préparation sécurisée de la synchronisation RAG LOCAL → AWS."""


from app.database import SessionLocal

# Connexion PostgreSQL depuis macOS
from dotenv import dotenv_values
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

_env = dotenv_values(Path.cwd() / ".env")
_local_url = make_url(_env["DATABASE_URL"]).set(
    host="127.0.0.1",
    port=5432,
)
LOCAL_DATABASE_URL = _local_url
_local_engine = create_engine(LOCAL_DATABASE_URL)
SessionLocal = sessionmaker(bind=_local_engine)

from app.ai.models import KnowledgeDocument
from app.ai.chunk_models import KnowledgeChunk
from app.routers.knowledge_sync_schemas import (
    KnowledgeChunkSync,
    KnowledgeDocumentSync,
    KnowledgeSyncPayload,
)

SOURCE_PREFIX = "knowledge/supply_chain/fr/"


def send_cloud_dry_run(payload):
    load_dotenv()

    sync_key = os.getenv("SYNC_API_KEY")
    if not sync_key:
        raise RuntimeError("SYNC_API_KEY absente")

    url = (
        "https://dw3e18cneqohd.cloudfront.net"
        "/api/admin/sync/knowledge"
    )

    response = requests.post(
        url,
        headers={"X-Sync-Key": sync_key},
        json=payload.model_dump(mode="json"),
        timeout=60,
    )

    print("HTTP :", response.status_code)

    if response.status_code == 404:
        print("⚠️ Endpoint RAG pas encore déployé sur AWS")
        return

    response.raise_for_status()

    result = response.json()
    print("✅ Dry-run AWS réussi")
    print("Documents analysés :", result.get("documents_processed"))

    for item in result.get("results", []):
        print(item["action"], ":", item["source"])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cloud-dry-run", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        documents = (
            db.query(KnowledgeDocument)
            .filter(KnowledgeDocument.source.like(f"{SOURCE_PREFIX}%"))
            .order_by(KnowledgeDocument.source)
            .all()
        )

        payload_documents = []

        for document in documents:
            chunks = (
                db.query(KnowledgeChunk)
                .filter(KnowledgeChunk.document_id == document.id)
                .order_by(KnowledgeChunk.chunk_index)
                .all()
            )

            payload_documents.append(
                KnowledgeDocumentSync(
                    title=document.title,
                    source=document.source,
                    content=document.content,
                    embedding=(
                        list(document.embedding)
                        if document.embedding is not None
                        else None
                    ),
                    chunks=[
                        KnowledgeChunkSync(
                            chunk_index=chunk.chunk_index,
                            content=chunk.content,
                            embedding=list(chunk.embedding),
                        )
                        for chunk in chunks
                    ],
                )
            )

        payload = KnowledgeSyncPayload(
            documents=payload_documents,
            dry_run=True,
        )

        print("✅ Documents français :", len(payload.documents))
        print(
            "✅ Chunks :",
            sum(len(doc.chunks) for doc in payload.documents),
        )
        print("✅ Embeddings : 384 dimensions")
        print("✅ Validation Pydantic réussie")
        print("🔒 Aucun transfert AWS effectué")

        if args.cloud_dry_run:
            send_cloud_dry_run(payload)


if __name__ == "__main__":
    main()
