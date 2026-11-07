# Sift

Sift is a modular, full-stack search engine built with Python, FastAPI, React 19, MongoDB, and Redis. It crawls web pages with `robots.txt` compliance, extracts content, builds an inverted index with positional tracking, caches query results in Redis, and ranks results using the BM25 probabilistic relevance algorithm.

Sift features both an interactive command-line interface with rich terminal formatting and a modern React web application backed by an asynchronous REST API with full pagination support and Docker containerization.

---

## Features

- **Web Crawling & Discovery**: Asynchronous crawler with `robots.txt` adherence (`urllib.robotparser`), per-domain crawl delays, and SHA-256 content hash deduplication.
- **Inverted Index with Positional Data**: Stores term frequencies, document frequencies, and word position lists (`positions`) in MongoDB to enable precise exact phrase search and proximity checks.
- **BM25 Ranking Algorithm**: Probabilistic relevance scoring with configurable parameters ($k_1 = 1.2, b = 0.75$), document length normalization, and cached inverse document frequencies (IDF).
- **Redis Result Caching**: High-performance caching layer in Redis for search query responses and term data, keyed by query hash, BM25 parameters ($k_1, b$), and index version with automated cache recovery and connection health checks.
- **Docker & Docker Compose Containerization**: Production-ready multi-service container setup (`Dockerfile` for backend, `Dockerfile` for frontend, and `docker-compose.yaml`) coordinating MongoDB 8.0, Redis 7 Alpine, the FastAPI search backend, and the React frontend with health checks and persistent volume storage.
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
├── .dockerignore            Root Docker build ignore rules
├── Dockerfile               Backend Python/FastAPI container definition
├── docker-compose.yaml      Multi-container orchestration (MongoDB, Redis, Backend, Frontend)
├── app.py                   FastAPI server entry point and lifespan manager
├── main.py                  CLI entry point for crawling, indexing, and interactive search
├── pyproject.toml           Python package configuration and dependencies
├── src/
│   ├── api/                 FastAPI web package
│   │   ├── routes.py        HTTP route definitions (/search with pagination and Redis cache)
│   │   └── schemas.py       Pydantic request and response schemas
│   ├── cache.py             Redis search result caching and cache-key generation
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
│   ├── mongodb.py           MongoDB connection lifecycle and Beanie initialization
│   └── redis.py             Redis connection manager and health check background task
├── frontend/                React 19 + TypeScript + Vite web interface
│   ├── .dockerignore        Frontend Docker build ignore rules
│   ├── Dockerfile           Frontend Node/Vite development container definition
│   ├── src/
│   │   ├── components/      Pagination, SearchBar, SearchResultItem, SearchResults
│   │   ├── styles/          Component-scoped CSS files (Pagination.css, SearchBar.css, etc.)
│   │   ├── lib/             API client with pagination, query parser, and favicon hooks
│   │   ├── types/           TypeScript interfaces (SearchResponse, SearchResult, etc.)
│   │   └── App.tsx          Main search interface state and layout
│   ├── package.json         Frontend dependencies and build scripts
│   └── README.md            Dedicated frontend documentation

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

You can run Sift using **Docker Compose** (recommended for a one-command full-stack setup) or set up the components **manually for local development**.

---

### Option A: Quick Start with Docker Compose (Recommended)

Docker Compose orchestrates the entire four-service Sift stack:

| Service | Image / Build | Port | Description |
|---|---|---|---|
| `mongodb` | `mongo:8.0` | `27017:27017` | Document database with healthcheck and persistent volume `mongodb_data` |
| `redis` | `redis:7-alpine` | `6379:6379` | In-memory cache for search queries with healthcheck |
| `backend` | `./Dockerfile` (`python:3.14-slim`) | `8000:8000` | FastAPI application with Beanie ODM and Redis client |
| `frontend` | `./frontend/Dockerfile` (`node:22-alpine`) | `5173:5173` | React 19 + Vite web interface bound to `0.0.0.0` |

#### 1. Configure Environment

Create a `.env` file in the repository root:

```env
MONGO_URI=mongodb://localhost:27017/sift
DATABASE_NAME=sift
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

*(When running inside Docker Compose, the `backend` container automatically overrides `MONGO_URI` to `mongodb://mongodb:27017/sift` and `REDIS_HOST` to `redis` via service discovery.)*

#### 2. Build and Start the Stack

```bash
docker compose up --build
```

Or run in detached mode in the background:

```bash
docker compose up -d --build
```

#### 3. Access Services

- **Web Search Interface**: [http://localhost:5173](http://localhost:5173)
- **FastAPI REST API**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

#### 4. Run Crawler & CLI inside Docker

To crawl seed pages and build the search index from inside the running backend container:

```bash
docker compose exec backend python main.py
```

To force a re-crawl and refresh of existing indexed pages:

```bash
docker compose exec backend python main.py --refresh
```

#### 5. Run Tests inside Docker

```bash
docker compose exec backend pytest
```

#### 6. Stop the Stack

```bash
docker compose down
```

To stop containers and also delete the persistent MongoDB data volume:

```bash
docker compose down -v
```

---

### Option B: Local Development (Without Docker)

#### Prerequisites

- **Python**: 3.11 or newer
- **MongoDB**: 6.0+ (running locally or via `docker compose up -d mongodb`)
- **Redis**: 7.0+ (running locally or via `docker compose up -d redis`)
- **Node.js**: 18+ and npm (for running the React frontend)

---

#### 1. Clone Repository & Setup Virtual Environment

```bash
git clone https://github.com/thaseenabbut/Sift.git
cd Sift
python3 -m venv .venv
source .venv/bin/activate
```

---

#### 2. Install Python Dependencies

Install Sift in editable mode with test dependencies:

```bash
pip install -e ".[test]"
```

Or install all runtime dependencies directly:

```bash
pip install fastapi uvicorn[standard] beanie motor pymongo redis python-dotenv beautifulsoup4 requests urllib3 rich nltk tldextract pydantic pytest pytest-asyncio httpx
```

*Note: Sift automatically downloads required NLTK tokenizers upon first run.*

---

#### 3. Start MongoDB & Redis

If MongoDB and Redis are not running as system services, start just the databases with Docker:

```bash
docker compose up -d mongodb redis
```

Or start them individually:

```bash
docker run -d --name sift-mongodb -p 27017:27017 mongo:8.0
docker run -d --name sift-redis -p 6379:6379 redis:7-alpine
```

---

#### 4. Configure Environment Variables

Create a `.env` file in the repository root:

```env
MONGO_URI=mongodb://localhost:27017/sift
DATABASE_NAME=sift
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
```

---

#### 5. Run the Crawler & CLI

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

#### 6. Run the FastAPI REST Server

Start the API server:

```bash
uvicorn app:app --reload
```
*(or run `python app.py`)*

- **API Base**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

#### 7. Run the React Frontend Web UI

In a separate terminal window:

```bash
cd frontend
npm install
npm run dev
```

Open your browser to **[http://localhost:5173](http://localhost:5173)** to access the web search interface. See [`frontend/README.md`](frontend/README.md) for full frontend documentation.

---

#### 8. Run Automated Tests

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