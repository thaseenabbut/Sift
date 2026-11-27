from .chunk import Chunk
from .page import Page
from .search_index import IndexStats, TermDocument

DOCUMENT_MODELS = [Page, TermDocument, IndexStats, Chunk]

__all__ = ["Chunk", "IndexStats", "Page", "TermDocument"]
