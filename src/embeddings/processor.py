from beanie import PydanticObjectId

from src.embeddings.generator import Generator
from storage.vectordb import VectorDB

generator = Generator()
vector_db = VectorDB()

async def process_page(page_id: PydanticObjectId, text):
    
    chunks, embeddings = generator.generate(text)
    
    if not chunks:
        return 

    await vector_db.save_chunks(
        page_id = page_id,
        chunks = chunks,
        embeddings = embeddings
    )