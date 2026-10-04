# Sift

Sift is a small, modular Python search-engine project. It crawls web pages,
builds an inverted index, and lets you query them from the command line using
BM25 ranking. The index is persisted to MongoDB via Beanie (an async ODM).

## Project structure

```text
main.py                  Application entry point
src/
  crawler.py             Document discovery and retrieval
  document_parser.py     Content extraction
  tokenizer.py           Text normalisation and tokenisation
  stemmer.py             Word stemming
  indexer.py             Inverted-index construction
  query_parser.py        Query parsing and operator handling
  retriever.py           Candidate retrieval and operator filtering
  ranker.py              BM25 scoring
  results.py             Result formatting and display
  search.py              Query execution pipeline
schemas/
  page.py                Page document schema (Beanie)
  search_index.py        SearchIndex document schema (Beanie)
  domain.py              Domain schema
  crawl_queue.py         Crawl queue schema
storage/
  mongodb.py             MongoDB connection and Beanie initialisation
data/                    Local, generated application data (git-ignored)
```

## Current features

- Web crawling and document discovery
- HTML content extraction
- Text tokenisation and stemming
- Inverted-index based retrieval
- BM25 ranking
- Query operators
- Required and excluded terms
- Exact phrase search
- Domain filtering with `site:`
- Title filtering with `intitle:`
- URL filtering with `inurl:`
- Related-term queries with `related:`
- Result snippets
- Query-term highlighting
- Persistent storage using MongoDB and Beanie

## Getting started

Sift targets Python 3.11 or newer and requires a running MongoDB instance.

### 1. Clone and create a virtual environment

```bash
git clone <repository-url>
cd Sift
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -e .
```

Or, if a `requirements.txt` is present:

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the repository root:

```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=sift
```

### 4. Run

```bash
python main.py
```

The application connects to MongoDB, crawls the configured seed pages, builds the search index, and enters an interactive command-line search loop.

Type `exit` or `quit` (or press `Ctrl-C`) to stop.

## Query syntax

Sift supports a Google-like query syntax:

| Syntax | Description |
|---|---|
| `python web` | Normal terms — ranked by BM25 |
| `+python` | Required term — document must contain it |
| `-java` | Excluded term — document must not contain it |
| `"search engine"` | Exact phrase match |
| `site:wikipedia.org` | Restrict results to a domain |
| `intitle:python` | Term must appear in the page title |
| `inurl:wiki` | Term must appear in the URL |
| `related:python` | Find pages related to a term |

## Search pipeline

Sift processes a search through several stages:

```text
Web Pages
    ↓
Crawler
    ↓
Document Parser
    ↓
Tokenizer / Stemmer
    ↓
Search Index
    ↓
Query Parser
    ↓
Retriever
    ↓
BM25 Ranker
    ↓
Result Generation
    ↓
CLI
```

The search index is persisted so that search data can be reused instead of rebuilding the entire index every time the application starts.

## Development

Keep reusable application logic in `src/` and use `main.py` only to wire the command-line interface to the application logic.

Data schemas live in `schemas/`, while MongoDB connection and persistence logic lives in `storage/`.

Generated indexes, crawler caches, and downloaded documents belong under `data/` and are intentionally excluded from version control.

## Roadmap

Planned improvements include:

- Graphical search interface
- Paginated search results
- Improved result presentation
- Semantic/vector search
- Hybrid keyword + semantic ranking
- Performance optimisations
- Rust-based components where performance justifies them
- Open-source release

## License

Sift is released under the [MIT License](LICENSE)