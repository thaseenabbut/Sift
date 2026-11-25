from typing import List
import pymongo
from pymongo import IndexModel
from beanie import Document, PydanticObjectId

class Chunk(Document):
    page_id: PydanticObjectId
    chunk_index: int
    text: str
    embedding: List[float]
    
    class Settings:
        name = "chunks"
        indexes = [
            IndexModel(
                [
                    ("page_id", pymongo.ASCENDING),
                    ("chunk_index", pymongo.ASCENDING),
                ],
                name="page_chunk_idx",
                unique=True,  # Prevents duplicate chunk numbers for the same page
            )
        ]
