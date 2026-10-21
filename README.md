# Sift

Sift is a modular, full-stack search engine built with Python, FastAPI, React 19, and MongoDB. It crawls web pages with `robots.txt` compliance, extracts content, builds an inverted index with positional tracking, and ranks results using the BM25 probabilistic relevance algorithm.

Sift features both an interactive command-line interface with rich terminal formatting and a modern React web application backed by an asynchronous REST API with full pagination support.

---

## Features

- **Web Crawling & Discovery**: Asynchronous crawler with `robots.txt` adherence (`urllib.robotparser`), per-domain crawl delays, and SHA-256 content hash deduplication.
- **Inverted Index with Positional Data**: Stores term frequencies, document frequencies, and word position lists (`positions`) in MongoDB to enable precise exact phrase search and proximity checks.
- **BM25 Ranking Algorithm**: Probabilistic relevance scoring with configurable parameters ($k_1 = 1.2, b = 0.75$), document length normalization, and cached inverse document frequencies (IDF).
- **Advanced Query Operators**:
  - Required terms (`+python`) and excluded terms (`-java`)
  - Exact phrase matching (`"machine learning"`)
  - Domain filtering (`site:wikipedia.org`)
  - Title filtering (`intitle:python`)
  - URL filtering (`inurl:wiki`)
  - Related term matching (`related:search`)
- **Server-Side & Client-Side Pagination**: Full pagination support through `page` and `page_size` query parameters on the API, paired with a React pagination component supporting numeric navigation, smart gap calculation, and smooth scrolling.
- **Index Integrity & Self-Repair**: Automated verification tools (`src/index_integrity.py`) to detect and heal missing postings or desynchronized index statistics.
- **FastAPI REST API**: Asynchronous search endpoint (`/search`) with pagination parameters, input validation, and interactive Swagger UI (`/docs`).
- **Modern React Web Frontend**: Clean, responsive search UI built with React 19, Vite, and TypeScript located in [`frontend/`](frontend/). Features live query parsing, term highlighting, favicon resolution, breadcrumbs, modular component CSS, and skeleton loading states.
- **Interactive Terminal CLI**: Built with `rich` for formatted results, clickable links, highlighted snippets, and interactive search loop.
- **Automated Testing Suite**: Thorough API test suite in `tests/test_search_api.py` covering happy paths, input validation, database failure modes, and regression scenarios.

---

## Project Structure

```text
Sift/
├── app.py                   FastAPI server entry point and lifespan manager
├── main.py                  CLI entry point for crawling, indexing, and interactive search
├── pyproject.toml           Python package configuration and dependencies
├── src/
│   ├── api/                 FastAPI web package
│   │   ├── routes.py        HTTP route definitions (/search with pagination)
│   │   └── schemas.py       Pydantic request and response schemas
│   ├── crawler.py           Web crawler, robots.txt handler, and seed processor
│   ├── document_parser.py   HTML parsing and SHA-256 content hashing
│   ├── indexer.py           Inverted-index builder and delta updater
│   ├── index_integrity.py   Index health auditing and automated repair
│   ├── query_parser.py      Search syntax parser for terms, phrases, and operators
│   ├── ranker.py            BM25 scoring, term collection, and IDF cache
│   ├── results.py           Context-aware snippet extraction and terminal highlighting
│   ├── retriever.py         Posting retrieval, candidate selection, and phrase verification
│   ├── search.py            End-to-end query execution pipeline
│   ├── stemmer.py           Porter stemmer integration
│   └── tokenizer.py         Regex-based tokenization and normalization
├── schemas/                 Beanie document models (MongoDB ODM)
│   ├── crawl_queue.py       Crawl task queue schema
│   ├── domain.py            Domain metadata, robot rules, and crawl delay schema
│   ├── page.py              Page document schema (title, clean text, content hash)
│   └── search_index.py      TermDocument, Posting, and IndexStats schemas
├── storage/
│   └── mongodb.py           MongoDB connection lifecycle and Beanie initialization
├── frontend/                React 19 + TypeScript + Vite web interface
│   ├── src/
│   │   ├── components/      Pagination, SearchBar, SearchResultItem, SearchResults
│   │   ├── styles/          Component-scoped CSS files (Pagination.css, SearchBar.css, etc.)
│   │   ├── lib/             API client with pagination and query parser
│   │   ├── types/           TypeScript interfaces (SearchResponse, SearchResult, etc.)
│   │   └── App.tsx          Main search interface state and layout
│   ├── package.json         Frontend dependencies and build scripts
│   └── README.md            Dedicated frontend documentation
└── tests/                   Pytest test suite
    ├── conftest.py          Shared test fixtures and database mocks
    └── test_search_api.py   Search API unit, validation, and regression tests
```

---

## Query Syntax

Sift supports a Google-like search syntax:

| Syntax | Description | Example |
|---|---|---|
| `terms` | Standard query terms — scored and ranked via BM25 | `python async web` |
| `+term` | **Required term** — document must contain this term | `+fastapi framework` |
| `-term` | **Excluded term** — documents containing this term are omitted | `python -snakes` |
| `"phrase"` | **Exact phrase** — matches words in precise sequential order | `"search engine"` |
| `site:domain` | **Domain filter** — restricts results to a specific host | `site:wikipedia.org` |
| `intitle:term` | **Title search** — term must appear in the document title | `intitle:python` |
| `inurl:term` | **URL search** — term must appear in the URL path or host | `inurl:wiki` |
| `related:term` | **Related terms** — finds documents mentioning related concepts | `related:database` |

*Operators can be combined freely, for example: `intitle:python "web framework" -flask site:wikipedia.org`.*

---

## Getting Started

### Prerequisites

- **Python**: 3.11 or newer
- **MongoDB**: 6.0+ (running locally or via Docker)
- **Node.js**: 18+ and npm (optional, for running the React frontend)

---

### 1. Clone Repository & Setup Virtual Environment

```bash
git clone https://github.com/thaseenabbut/Sift.git
cd Sift
python3 -m venv .venv
source .venv/bin/activate
```

---

### 2. Install Python Dependencies

Install Sift in editable mode with development/test dependencies:

```bash
pip install -e ".[test]"
```

Or install the required packages directly:

```bash
pip install fastapi uvicorn[standard] motor beanie beautifulsoup4 nltk rich requests tldextract pydantic pytest pytest-asyncio httpx
```

*Note: Sift automatically downloads required NLTK tokenizers upon first run.*

---

### 3. Start MongoDB

If MongoDB is not installed as a system service, start an instance via Docker:

```bash
docker run -d --name sift-mongo -p 27017:27017 mongo:latest
```

---

### 4. Configure Environment Variables

Create a `.env` file in the repository root:

```env
MONGO_URI=mongodb://localhost:27017
DATABASE_NAME=sift
```

---

### 5. Run the Crawler & CLI

To crawl seed pages, build the index, and launch the interactive terminal search shell:

```bash
python main.py
```

To force a re-crawl and refresh of existing seed URLs:

```bash
python main.py --refresh
```

Type `exit`, `quit`, or press `Ctrl-C` to exit the CLI loop.

---

### 6. Run the FastAPI REST Server

Start the API server:

```bash
uvicorn app:app --reload
```

- **API Base**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Alternative ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### 7. Run the React Frontend Web UI

In a new terminal window:

```bash
cd frontend
npm install
npm run dev
```

Open your browser to **[http://localhost:5173](http://localhost:5173)** to access the web search interface. See [`frontend/README.md`](frontend/README.md) for full frontend documentation.

---

### 8. Run Automated Tests

Run the test suite using `pytest`:

```bash
pytest
```

---

## REST API Reference

### `GET /search`

Searches the indexed corpus using BM25 scoring, operator filtering, and server-side pagination.

#### Query Parameters

| Parameter | Type | Required | Default | Description |
|---|---|---|---|---|
| `q` | `string` | **Yes** | — | Search query string (minimum length 1) |
| `page` | `integer` | No | `1` | Page number to retrieve ($\ge 1$) |
| `page_size` | `integer` | No | `10` | Maximum results per page ($1 \le \text{page\_size} \le 100$) |

#### Example Request

```http
GET /search?q=python+programming&page=1&page_size=10 HTTP/1.1
Host: 127.0.0.1:8000
```

#### Example Response (`200 OK`)

```json
{
  "query": "python programming",
  "count": 2,
  "total": 2,
  "page": 1,
  "page_size": 10,
  "results": [
    {
      "title": "Python (programming language) - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Python_(programming_language)",
      "snippet": "Python is a high-level, general-purpose programming language. Its design philosophy emphasizes code readability...",
      "score": 14.8219
    },
    {
      "title": "Programming language - Wikipedia",
      "url": "https://en.wikipedia.org/wiki/Programming_language",
      "snippet": "A programming language is a system of notation for writing computer programs...",
      "score": 9.4031
    }
  ]
}
```

#### Error Responses

| Status Code | Reason | Detail |
|---|---|---|
| `400 Bad Request` | Empty query after trimming | `"Search query cannot be empty."` |
| `422 Unprocessable Entity` | Parameter validation failure | Query missing, `page < 1`, or `page_size` out of bounds |
| `503 Service Unavailable` | DB connection failure or missing index | `"Search service is temporarily unavailable."` / `"Search index is not available."` |
| `500 Internal Server Error` | Unexpected processing error | `"An unexpected error occurred while searching."` |

---

## License

Sift is open-source software licensed under the [MIT License](LICENSE).