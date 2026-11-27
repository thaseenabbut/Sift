import numpy as np
from beanie import PydanticObjectId

from schemas.chunk import Chunk


class VectorDB:
    async def delete_chunks(self, page_id: PydanticObjectId) -> int:
        """Delete every vector belonging to a page and return the count."""
        result = await Chunk.get_pymongo_collection().delete_many({"page_id": page_id})
        return result.deleted_count

    async def replace_chunks(
        self,
        page_id: PydanticObjectId,
        chunks: list[str],
        embeddings: np.ndarray,
    ) -> int:
        if len(chunks) != len(embeddings):
            raise ValueError("Chunk and embedding counts must match.")

        await self.delete_chunks(page_id)
        if not chunks:
            return 0

        documents = []

        for i, chunk in enumerate(chunks):
            embedding = embeddings[i]

            chunk_doc = Chunk(
                page_id=page_id,
                chunk_index=i,
                text=chunk,
                embedding=embedding.tolist()
            )

            documents.append(chunk_doc)

        await Chunk.insert_many(documents)
        return len(documents)

    async def save_chunks(self, page_id: PydanticObjectId, chunks: list[str], embeddings: np.ndarray):
        """Backward-compatible alias for replacement semantics."""
        return await self.replace_chunks(page_id, chunks, embeddings)

    async def search_similar(self, query_embedding: np.ndarray, limit: int = 10) -> list[dict]:
        
        query_vector = query_embedding.squeeze().tolist()
        
        pipeline = [
    {
        "$vectorSearch": {
            "index": "vector_index",
            "path": "embedding",
            "queryVector": query_vector,
            "numCandidates": max(100, limit * 15),
            "limit": limit
        }
    },
    {
                "$project": {
                    "_id": 0,
                    "page_id": 1,
                    "chunk_index": 1,
                    "text": 1,
                    "score": {"$meta": "vectorSearchScore"},
                }
            },
        ]
        
        return await Chunk.aggregate(pipeline).to_list()
