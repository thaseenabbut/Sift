import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from crawler import crawl
from indexer import index
from search import search
from ranker import bm25_parameters
from rich import print

def main():
    seed_urls = [
        "https://en.wikipedia.org/wiki/Python_(programming_language)",
        "https://en.wikipedia.org/wiki/JavaScript",
        "https://en.wikipedia.org/wiki/Programming_language",
        "https://en.wikipedia.org/wiki/Software_engineering",
        "https://en.wikipedia.org/wiki/Search_engine",
    ]
    
    print("Crawling pages...")
    pages = crawl(seed_urls, max_pages=20)
    
    print(f"Indexing {len(pages)} pages...")
    search_index = index(pages)
    
    print("Sift Search Engine is ready!")
    print("Type 'exit' or 'quit' to stop.")
    
    while True:
        try:
            query = input("\nEnter search query: ").strip()
            if query.lower() in ['exit', 'quit']:
                break
            if not query:
                continue
                
            search(query, search_index, bm25_parameters, pages)
            
        except KeyboardInterrupt:
            print("[bold red]Exiting...[/bold red]")
            break
        except EOFError:
            break
        except Exception as e:
            print(f"[bold red]An error occurred:[/bold red] {e}")

if __name__ == "__main__":
    main()
