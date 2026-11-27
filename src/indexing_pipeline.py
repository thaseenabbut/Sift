"""Coordinates lexical and vector indexing for persisted pages."""

from dataclasses import dataclass
import logging
from collections.abc import Awaitable, Callable
from typing import Any

from rich import print as rich_print

from schemas.page import Page
from src.embeddings.processor import ChunkProcessingResult, process_page
from src.indexer import index_page
from storage.vectordb import VectorDB

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IndexingResult:
    bm25_indexed: bool
    chunks_generated: int = 0
    embeddings_saved: int = 0
    chunks_skipped: bool = False


class PageIndexingPipeline:
    """Keep BM25 and vector updates coordinated without coupling the crawler.

    A vector failure deliberately leaves ``chunk_content_hash`` stale.  The
    next crawl or explicit reindex will retry it instead of reporting the page
    as fully indexed.
    """

    def __init__(
        self,
        vector_db: VectorDB | None = None,
        *,
        bm25_indexer: Callable[[Page], Awaitable[Any]] = index_page,
        chunk_processor: Callable[..., Awaitable[ChunkProcessingResult]] = process_page,
    ):
        self.vector_db = vector_db or VectorDB()
        self._bm25_indexer = bm25_indexer
        self._chunk_processor = chunk_processor

    async def index_page(
        self,
        page: Page,
        *,
        rebuild_bm25: bool,
        rebuild_chunks: bool,
        force_chunks: bool = False,
    ) -> IndexingResult:
        bm25_indexed = False
        if rebuild_bm25:
            await self._bm25_indexer(page)
            bm25_indexed = True

        if not rebuild_chunks or (
            not force_chunks and page.chunk_content_hash == page.content_hash
        ):
            return IndexingResult(
                bm25_indexed=bm25_indexed,
                chunks_skipped=True,
            )

        # A changed Page must never continue serving old chunks.  If generation
        # or insertion fails, the stale hash makes this retryable on the next
        # run and the page is surfaced as an indexing failure to the caller.
        rich_print(
            "[bold cyan][VECTOR INDEX][/bold cyan] "
            f"Generating chunks and embeddings: {page.url}"
        )
        await self.vector_db.delete_chunks(page.id)
        if not isinstance(page.clean_text, str) or not page.clean_text.strip():
            # Empty pages are valid crawl records, but there is no meaningful
            # passage to embed.  Treat the empty vector set as the complete
            # representation for this content hash so backfills do not retry
            # the same page forever.
            page.chunk_content_hash = page.content_hash
            await page.save()
            rich_print(
                "[bold yellow][VECTOR INDEX][/bold yellow] "
                f"No embeddable text; saved empty chunk set: {page.url}"
            )
            logger.info("Skipped vector generation for empty page url=%s id=%s", page.url, page.id)
            return IndexingResult(
                bm25_indexed=bm25_indexed,
                chunks_skipped=False,
            )
        try:
            processed: ChunkProcessingResult = await self._chunk_processor(
                page.id,
                page.clean_text,
                self.vector_db,
            )
        except Exception:
            logger.exception("Vector indexing failed for page url=%s id=%s", page.url, page.id)
            raise

        page.chunk_content_hash = page.content_hash
        await page.save()
        rich_print(
            "[bold green][VECTOR INDEX][/bold green] "
            f"Saved {processed.chunks_generated} chunk(s) and "
            f"{processed.embeddings_saved} embedding(s): {page.url}"
        )
        logger.info(
            "Vector indexed page url=%s chunks=%s embeddings=%s",
            page.url,
            processed.chunks_generated,
            processed.embeddings_saved,
        )
        return IndexingResult(
            bm25_indexed=bm25_indexed,
            chunks_generated=processed.chunks_generated,
            embeddings_saved=processed.embeddings_saved,
        )
