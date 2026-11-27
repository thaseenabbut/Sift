import pymongo
from beanie import Document, PydanticObjectId
from pymongo import IndexModel


class Chunk(Document):
    page_id: PydanticObjectId
    chunk_index: int
    text: str
    embedding: list[float]
    
    class Settings:
        name = "chunks"
        indexes = [  # noqa: RUF012
            IndexModel(
                [
                    ("page_id", pymongo.ASCENDING),
                    ("chunk_index", pymongo.ASCENDING),
                ],
                name="page_chunk_idx",
                unique=True,  # Prevents duplicate chunk numbers for the same page
            )
        ]
