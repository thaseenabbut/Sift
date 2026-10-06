from .crawl_queue import CrawlQueue
from .domain import Domain
from .page import Page
from .search_index import TermDocument, IndexStats

DOCUMENT_MODELS = [CrawlQueue, Domain, Page, TermDocument, IndexStats]

__all__ = ["CrawlQueue", "Domain", "Page", "TermDocument", "IndexStats"]
