from pydantic import BaseModel, Field, field_validator


class KnowledgeChunkSync(BaseModel):
    chunk_index: int = Field(ge=0)
    content: str = Field(min_length=1)
    embedding: list[float] = Field(min_length=384, max_length=384)

    @field_validator("embedding")
    @classmethod
    def validate_embedding(cls, value: list[float]) -> list[float]:
        import math

        if not all(math.isfinite(x) for x in value):
            raise ValueError("Embedding contains non-finite values")
        return value


class KnowledgeDocumentSync(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    source: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    embedding: list[float] | None = Field(default=None, min_length=384, max_length=384)
    chunks: list[KnowledgeChunkSync] = Field(min_length=1)

    @field_validator("source")
    @classmethod
    def validate_source(cls, value: str) -> str:
        if not value.startswith("knowledge/supply_chain/fr/"):
            raise ValueError("Only French Supply Chain documents are allowed")
        return value


class KnowledgeSyncPayload(BaseModel):
    documents: list[KnowledgeDocumentSync] = Field(min_length=1, max_length=20)
    dry_run: bool = True
