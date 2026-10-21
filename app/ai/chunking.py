import re

from app.ai.embeddings import _model

CHUNK_SIZE = 160
CHUNK_OVERLAP = 24


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping, sentence-aware chunks."""

    if not text or not text.strip():
        return []

    tokenizer = _model.tokenizer
    # Reserve a safety margin for tokenization differences
    # when multiple sentences are joined into one chunk.
    max_tokens = min(
        CHUNK_SIZE,
        _model.max_seq_length - tokenizer.num_special_tokens_to_add(pair=False) - 8,
    )

    if max_tokens <= CHUNK_OVERLAP:
        raise ValueError("Chunk overlap must be smaller than chunk size.")

    sentences = re.split(r"(?<=[.!?])\\s+|\\n+", text.strip())
    sentences = [sentence.strip() for sentence in sentences if sentence.strip()]

    units = []

    for sentence in sentences:
        ids = tokenizer.encode(
            sentence,
            add_special_tokens=False,
            truncation=False,
        )

        if len(ids) <= max_tokens:
            units.append(sentence)
            continue

        for start in range(0, len(ids), max_tokens):
            part = tokenizer.decode(
                ids[start:start + max_tokens],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True,
            ).strip()

            if part:
                units.append(part)

    chunks = []
    current = []
    current_tokens = 0

    for unit in units:
        unit_tokens = len(
            tokenizer.encode(unit, add_special_tokens=False, truncation=False)
        )

        if current and current_tokens + unit_tokens > max_tokens:
            chunks.append(" ".join(current))

            overlap = []
            overlap_tokens = 0

            for previous in reversed(current):
                count = len(
                    tokenizer.encode(
                        previous,
                        add_special_tokens=False,
                        truncation=False,
                    )
                )

                if overlap_tokens + count > CHUNK_OVERLAP:
                    break

                overlap.insert(0, previous)
                overlap_tokens += count

            current = overlap
            current_tokens = overlap_tokens

        current.append(unit)
        current_tokens += unit_tokens

    if current:
        chunks.append(" ".join(current))

    return chunks
