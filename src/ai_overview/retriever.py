
from schemas.page import Page
from src.retrieval.semantic import semantic_search
from storage.vectordb import VectorDB


async def retrieve_chunks(
    query: str,
    vector_db: VectorDB,
    limit: int = 50,
) -> list[dict]:

    chunks = await semantic_search(
        query=query,
        vector_db=vector_db,
        limit=limit,
    )

    if not chunks:
        return []

    page_ids = list(
        dict.fromkeys(chunk["page_id"] for chunk in chunks)
    )

    pages = await Page.find(
        {"_id": {"$in": page_ids}}
    ).to_list()

    page_lookup = {
        str(page.id): page
        for page in pages
    }

    retrieved_chunks = []

    for chunk in chunks:
        page = page_lookup.get(str(chunk["page_id"]))

        # it never create a citation without a real source page
        if page is None:
            continue

        retrieved_chunks.append({
            "text": chunk["text"],
            "score": chunk["score"],
            "chunk_index": chunk["chunk_index"],
            "page_id": str(page.id),
            "title": page.title,
            "url": page.url,
        })

    return retrieved_chunks
