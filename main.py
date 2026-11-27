import argparse
import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from rich import print
from rich.console import Console

from schemas.page import Page
from schemas.search_index import IndexStats
from src.crawler import CrawlSummary, already_indexed_urls, crawl, filter_seed_urls
from src.indexing_pipeline import PageIndexingPipeline
from src.ranker import bm25_parameters, proximity_weight
from src.search import search
from storage.mongodb import db_manager
from storage.redis import redis_manager

console = Console()

def parse_args():
    parser = argparse.ArgumentParser(description="Sift search engine")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-crawl and re-index existing seed URLs",
    )
    parser.add_argument(
        "--no-crawl",
        action="store_true",
        help="Skip all crawling and use the existing index as-is",
    )
    parser.add_argument(
        "--reindex",
        action="store_true",
        help="Force BM25 and vector reindexing for every stored Page without crawling",
    )
    return parser.parse_args()

async def force_reindex_all_pages() -> CrawlSummary:
    """Stream stored pages through both indexes without loading the corpus."""
    pipeline = PageIndexingPipeline()
    summary = CrawlSummary()
    pages = Page.find_all()
    total_pages = await pages.count()
    print(f"[bold blue][FULL REINDEX][/bold blue] Processing {total_pages} stored page(s).")
    processed_pages = 0
    async for page in pages:
        processed_pages += 1
        print(
            "[bold blue][FULL REINDEX][/bold blue] "
            f"[{processed_pages}/{total_pages}] {page.url}"
        )
        summary.urls_discovered += 1
        try:
            indexing = await pipeline.index_page(
                page,
                rebuild_bm25=True,
                rebuild_chunks=True,
                force_chunks=True,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[bold red][REINDEX FAILED][/bold red] {page.url}: {exc}")
            summary.failed_pages.append(page.url)
            summary.indexing_failures.append(f"{page.url}: {exc}")
            continue

        summary.pages_successfully_crawled += 1
        summary.pages_indexed_bm25 += int(indexing.bm25_indexed)
        summary.pages_processed_chunking += int(not indexing.chunks_skipped)
        summary.total_chunks_generated += indexing.chunks_generated
        summary.total_embeddings_saved += indexing.embeddings_saved
    summary.print_final()
    return summary


async def backfill_missing_chunks() -> CrawlSummary:
    """Stream only pages without chunks for their current content hash."""
    pipeline = PageIndexingPipeline()
    summary = CrawlSummary()
    stale_chunks_filter = {
        "$expr": {"$ne": ["$chunk_content_hash", "$content_hash"]},
    }
    print("[bold blue][CHUNK BACKFILL][/bold blue] Scanning for missing or stale vectors...")
    pages = Page.find(stale_chunks_filter)
    total_pages = await pages.count()
    if not total_pages:
        print("[bold green][CHUNK BACKFILL][/bold green] All stored pages already have current vectors.")
        return summary

    print(f"[bold blue][CHUNK BACKFILL][/bold blue] Processing {total_pages} page(s).")
    processed_pages = 0
    async for page in pages:
        processed_pages += 1
        print(
            "[bold blue][CHUNK BACKFILL][/bold blue] "
            f"[{processed_pages}/{total_pages}] {page.url}"
        )
        summary.urls_discovered += 1
        try:
            indexing = await pipeline.index_page(
                page,
                rebuild_bm25=False,
                rebuild_chunks=True,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"[bold red][CHUNK BACKFILL FAILED][/bold red] {page.url}: {exc}")
            summary.failed_pages.append(page.url)
            summary.indexing_failures.append(f"{page.url}: {exc}")
            continue

        summary.pages_successfully_crawled += 1
        summary.pages_processed_chunking += int(not indexing.chunks_skipped)
        summary.total_chunks_generated += indexing.chunks_generated
        summary.total_embeddings_saved += indexing.embeddings_saved

    if summary.urls_discovered:
        print("[bold blue][CHUNK BACKFILL][/bold blue] Completed stale/missing vector scan.")
        summary.print_final()
    return summary


async def main(refresh_existing=False, no_crawl=False, reindex=False):
    await redis_manager.connect_redis()
    await db_manager.connect_and_init()
    stats = await IndexStats.find_one({"id_name": "global_stats"})

    
    with open('data/seed_urls.txt', 'r') as f:  # noqa: ASYNC230
        seed_urls = [line.strip() for line in f]
    
    if reindex:
        summary = await force_reindex_all_pages()
        if summary.pages_indexed_bm25:
            stats = await IndexStats.find_one({"id_name": "global_stats"})
            if stats is not None:
                stats.index_version += 1
                await stats.save()
                print(f"[bold green][INDEX VERSION][/bold green] Updated to v{stats.index_version}")
    elif no_crawl:
        if stats and stats.total_documents > 0:
            print(f"[bold yellow][--no-crawl][/bold yellow] Skipping all crawling. Using existing index ({stats.total_documents} document(s)).")
        else:
            print("[bold yellow][--no-crawl][/bold yellow] Skipping all crawling, but no existing index found. Nothing to search.")
    else:
        indexed_urls = await already_indexed_urls()
        urls_to_crawl = filter_seed_urls(seed_urls, indexed_urls, refresh_existing)

        if stats and stats.total_documents > 0:
            print("Existing index found.")

        if refresh_existing:
            urls_to_crawl = seed_urls
            print(f"Refreshing {len(urls_to_crawl)} seed URL(s)...")
        elif urls_to_crawl:
            print(f"Crawling {len(urls_to_crawl)} new seed URL(s)...")

        if urls_to_crawl:
            crawl_summary = await crawl(
                urls_to_crawl,
                max_pages=1000000,
                refresh_existing=refresh_existing,
            )
            if crawl_summary.pages_indexed_bm25 > 0:
                stats = await IndexStats.find_one({"id_name": "global_stats"})
                
                if stats is not None:
                    stats.index_version += 1
                    await stats.save()
                    print(f"[bold green][INDEX VERSION][/bold green] Updated to v{stats.index_version}")
                    
            print(f"Indexed {crawl_summary.pages_successfully_crawled} page(s).")
        elif not stats or stats.total_documents == 0:
            print("No index found and no seed URLs to crawl.")
        else:
            print("No new seed URLs to crawl. Use [bold yellow]--refresh[/bold yellow] to re-index existing seeds.")

        backfill_summary = await backfill_missing_chunks()
        if backfill_summary.pages_processed_chunking:
            stats = await IndexStats.find_one({"id_name": "global_stats"})
            if stats is not None:
                stats.index_version += 1
                await stats.save()
                print(f"[bold green][INDEX VERSION][/bold green] Updated to v{stats.index_version}")
    
    print("[bold green][ONLINE][/bold green] Sift Search Engine is ready!")
    print("Type 'exit' or 'quit' to stop.")
    
    while True:
        try:
            query = input("\nEnter search query: ").strip()
            if query.lower() in ['exit', 'quit']:
                break
            if not query:
                continue
            
            await search(query, bm25_parameters, redis_manager, proximity_weight)
            
        except KeyboardInterrupt:
            print("[bold red]Exiting...[/bold red]")
            break
        except EOFError:
            break
        except (ValueError, RuntimeError):
            console.print_exception()
            
    await redis_manager.close_redis()
    await db_manager.close_connection()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        main(
            refresh_existing=args.refresh,
            no_crawl=args.no_crawl,
            reindex=args.reindex,
        )
    )
