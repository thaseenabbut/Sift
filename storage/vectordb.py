import numpy as np
from beanie import PydanticObjectId

from schemas.chunk import Chunk


class VectorDB:
    async def save_chunks(self, page_id: PydanticObjectId, chunks: list[str], embeddings: np.ndarray):
        
        if not chunks:
            return
        
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
    