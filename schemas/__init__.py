from .chunk import Chunk
from .crawl_queue import CrawlQueue
from .domain import Domain
from .page import Page
from .search_index import IndexStats, TermDocument

DOCUMENT_MODELS = [CrawlQueue, Domain, Page, TermDocument, IndexStats, Chunk]

__all__ = ["Chunk", "CrawlQueue", "Domain", "IndexStats", "Page", "TermDocument"]
