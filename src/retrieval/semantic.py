from src.embeddings.model import embed_query
from storage.vectordb import VectorDB

vector_db = VectorDB()

async def semantic_search(query: str, vector_db: VectorDB, limit: int = 50):
    query_embedding = embed_query(query)

    similar_chunks = await vector_db.search_similar(
        query_embedding,
        limit=limit,
    )

    return similar_chunks
