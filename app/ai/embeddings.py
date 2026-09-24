from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSION = 384

_model = SentenceTransformer(MODEL_NAME)


def generate_embedding(text: str) -> list[float]:
    embedding = _model.encode(text)

    if len(embedding) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Expected {EMBEDDING_DIMENSION} dimensions, got {len(embedding)}"
        )

    return embedding.tolist()
