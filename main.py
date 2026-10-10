import sys
import os
import argparse
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.crawler import crawl, normalize_url, already_indexed_urls
from src.search import search
from src.ranker import bm25_parameters

from rich import print
from rich.console import Console

from storage.mongodb import db_manager
from schemas.search_index import IndexStats

console = Console()

def parse_args():
    parser = argparse.ArgumentParser(description="Sift search engine")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-crawl and re-index existing seed URLs",
    )
    return parser.parse_args()

async def main(refresh_existing=False):
    await db_manager.connect_and_init()
    stats = await IndexStats.find_one(
    IndexStats.id_name == "global_stats"
)

    
    seed_urls = [
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://en.wikipedia.org/wiki/JavaScript",
        "https://en.wikipedia.org/wiki/Programming_language",
        "https://en.wikipedia.org/wiki/Software_engineering",
        "https://en.wikipedia.org/wiki/Search_engine",
        "https://thaseenabbut.github.io/LazaBot-Legal/",
    ]
    
    indexed_urls = await already_indexed_urls()
    new_seed_urls = [
        url for url in seed_urls
        if normalize_url(url) not in indexed_urls
    ]

    if stats and stats.total_documents > 0:
        print("[bold yellow][INDEXED][/bold yellow] Existing index found.")

    if refresh_existing:
        urls_to_crawl = seed_urls
        print(f"Refreshing {len(urls_to_crawl)} seed URL(s)...")
    else:
        urls_to_crawl = new_seed_urls
        if urls_to_crawl:
            print(f"Crawling {len(urls_to_crawl)} new seed URL(s)...")

    if urls_to_crawl:
        with console.status("[bold green]Crawling and indexing pages...[/bold green]", spinner="dots"):
            crawled = await crawl(
                urls_to_crawl,
                max_pages=20,
                refresh_existing=refresh_existing,
            )
        print(f"Indexed {crawled} page(s).")
    elif not stats or stats.total_documents == 0:
        print("No index found and no seed URLs to crawl.")
    else:
        print("No new seed URLs to crawl. Use [bold yellow]--refresh[/bold yellow] to re-index existing seeds.")
    
    print("[bold green][ONLINE][/bold green] Sift Search Engine is ready!")
    print("Type 'exit' or 'quit' to stop.")
    
    while True:
        try:
            query = input("\nEnter search query: ").strip()
            if query.lower() in ['exit', 'quit']:
                break
            if not query:
                continue
                
            await search(query, bm25_parameters)
            
        except KeyboardInterrupt:
            print("[bold red]Exiting...[/bold red]")
            break
        except EOFError:
            break
        except Exception as e:
            console.print_exception()
            
    await db_manager.close_connection()

if __name__ == "__main__":
    args = parse_args()
    asyncio.run(main(refresh_existing=args.refresh))