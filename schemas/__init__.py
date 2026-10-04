from .crawl_queue import CrawlQueue
from .page import Page
from .seeds import SEED_URLS

DOCUMENT_MODELS = [CrawlQueue, Page]

__all__ = ["CrawlQueue", "Page", "SEED_URLS"]
