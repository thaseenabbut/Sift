import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.crawler import crawl
from src.search import search
from src.ranker import bm25_parameters
from rich import print

from storage.mongodb import db_manager
from schemas.search_index import IndexStats

async def main():
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
    ]
    
    if stats and stats.total_documents > 0:
        print("Existing index found.")
    else:
        print("No index found. Starting initial crawl...")
        print("Crawling and indexing pages...")
        await crawl(seed_urls, max_pages=20)
    
    print("Sift Search Engine is ready!")
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
            print(f"[bold red]An error occurred:[/bold red] {e}")
            
    await db_manager.close_connection()

if __name__ == "__main__":
    asyncio.run(main())
