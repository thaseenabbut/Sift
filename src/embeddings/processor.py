from beanie import PydanticObjectId
from dataclasses import dataclass

import numpy as np

from src.embeddings.generator import Generator
from storage.vectordb import VectorDB

generator = Generator()
vector_db = VectorDB()

@dataclass(frozen=True)
class ChunkProcessingResult:
    chunks_generated: int
    embeddings_saved: int


async def process_page(
    page_id: PydanticObjectId,
    text: str,
    storage: VectorDB | None = None,
) -> ChunkProcessingResult:
    """Generate and replace the complete vector representation of one page."""
    if not isinstance(text, str) or not text.strip():
        saved = await (storage or vector_db).replace_chunks(
            page_id=page_id,
            chunks=[],
            embeddings=np.empty((0, 0)),
        )
        return ChunkProcessingResult(chunks_generated=0, embeddings_saved=saved)

    chunks, embeddings = generator.generate(text)
    saved = await (storage or vector_db).replace_chunks(
        page_id = page_id,
        chunks = chunks,
        embeddings = embeddings
    )
    return ChunkProcessingResult(
        chunks_generated=len(chunks),
        embeddings_saved=saved,
    )
