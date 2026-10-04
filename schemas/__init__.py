from .crawl_queue import CrawlQueue
from .domain import Domain
from .page import Page
from .search_index import SearchIndex

DOCUMENT_MODELS = [CrawlQueue, Domain, Page, SearchIndex]

__all__ = ["CrawlQueue", "Domain", "Page", "SearchIndex"]
