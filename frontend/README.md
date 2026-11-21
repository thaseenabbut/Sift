# Sift Frontend

A fast, responsive, and minimalist web search interface for the **Sift** search engine, built with **React 19**, **TypeScript**, and **Vite**.

---

## Overview

The Sift frontend connects to the Sift FastAPI backend to deliver a Google-like search experience. It features a clean dual-mode interface (hero homepage transitioning into a focused results layout), instant client-side query term highlighting, smart breadcrumb URL parsing, domain favicon fetching, skeleton loading states, race-condition-safe request dispatching, full client-side and server-side pagination, search execution latency display, and comprehensive error resilience with specialized views for rate limits and service outages.

---

## Features

- **Dual-State Interface**: Clean, centered hero landing view that smoothly transitions into a sticky top masthead with results upon search submission.
- **Client-Side Query Parsing & Highlighting**: Automatically extracts quoted phrases, normal terms, and operators (e.g. `intitle:`) to dynamically highlight matching text in result titles and snippets using `<mark>`.
- **Search Execution Latency**: Real-time display of backend query performance metrics (`About X results (0.02 seconds) for "query"`).
- **Smart Numeric Pagination**: Seamless multi-page browsing via `<Pagination />` featuring Previous/Next navigation, active page indicators (`aria-current="page"`), sibling windowing with ellipsis gaps (`…`), and smooth scroll-to-top on page transitions.
- **Dedicated Error Resilience & Rate Limit Recovery**:
  - **429 Rate Limiting**: Intercepts HTTP 429 responses, extracts `Retry-After` headers, and renders a dedicated `<TooManyRequests />` page with a live countdown timer and retry mechanism.
  - **503 Outage Handling**: Renders a dedicated `<ServiceUnavailable />` screen when the backend database or search index is unreachable, with automated and manual retry triggers.
- **Client-Side SPA Routing**: Built on **React Router 7** with dedicated routes for `/` (home), `/search` (results view), `/about`, `/terms`, `/privacy`, and wildcard 404 (`/not-found`).
- **URL & Breadcrumb Parsing**: Parses result URLs to extract the clean site name, domain origin, and path breadcrumbs (`example.com › docs › api`).
- **Favicon Resolution**: Fetches high-resolution site favicons dynamically with automatic fallback on load failure.
- **Race Condition Prevention**: Employs monotonic request IDs (`requestId.current`) to discard outdated, slower responses when rapid successive queries or page changes occur.
- **Docker Containerization**: Self-contained `node:22-alpine` container configuration with volume mounting and host binding (`--host 0.0.0.0`) for instant setup and multi-container orchestration.
- **Modular Component CSS**: Component-scoped and page-scoped stylesheets located in `src/styles/` for clean separation of concerns and maintainability.
- **Accessible & Semantic UX**: Includes proper ARIA attributes (`role="search"`, `aria-busy`, `aria-live="polite"`, `aria-label`), animated skeleton placeholders during loading, and clear empty/error notices.
- **Dynamic Document Title**: Updates browser tab title to reflect the active search query (`{query} - Sift Search`).

---

## Tech Stack

| Technology | Purpose |
|---|---|
| **[React 19](https://react.dev/)** | Core UI component library |
| **[React Router 7](https://reactrouter.com/)** | Client-side routing, URL state synchronization, and page navigation |
| **[TypeScript](https://www.typescriptlang.org/)** | Static type checking and safety |
| **[Vite 8](https://vite.dev/)** | Lightning-fast build tool and local dev server |
| **[Docker](https://www.docker.com/)** | Containerized dev environment using `node:22-alpine` |
| **[Oxlint](https://oxc.rs/)** | High-performance JavaScript/TypeScript linter |
| **Vanilla CSS** | Component-scoped stylesheets and custom design system |

---

## Directory Structure

```text
frontend/
├── public/                 Static public assets (favicons, icons)
├── src/
│   ├── assets/             Frontend assets
│   ├── components/         Reusable React components
│   │   ├── AIOverview.tsx         AI overview summary component
│   │   ├── Pagination.tsx         Multi-page navigation controls and ellipsis logic
│   │   ├── SearchBar.tsx          Search input form with SVG search icon
│   │   ├── SearchResultItem.tsx   Individual result card with favicon, title, snippet, and highlights
│   │   └── SearchResults.tsx      Results list container, pagination wrapper, timing metrics, and skeleton loader
│   ├── pages/              Full-page informational and error screens
│   │   ├── about.tsx              About page
│   │   ├── not-found.tsx          404 not found page
│   │   ├── privacy.tsx            Privacy policy page
│   │   ├── service-unavailable.tsx 503 Service unavailable screen with retry
│   │   ├── terms.tsx              Terms of service page
│   │   └── too-many-requests.tsx  429 Too many requests screen with countdown timer
│   ├── styles/             Component-scoped and page-scoped stylesheets
│   │   ├── about.css              About page styling
│   │   ├── not-found.css          404 page styling
│   │   ├── Pagination.css         Pagination bar and button styles
│   │   ├── privacy.css            Privacy policy styling
│   │   ├── SearchBar.css          Search input and icon styles
│   │   ├── SearchResultItem.css   Result item, favicon, snippet, and highlight mark styles
│   │   ├── SearchResults.css      Result list layout, summary, and notice styles
│   │   ├── service-unavailable.css 503 error page styling
│   │   ├── terms.css              Terms page styling
│   │   └── too-many-requests.css  429 rate limit error page styling
│   ├── lib/                Utility and helper functions
│   │   ├── api.ts                 Backend API client with pagination, error parsing, and retry-after support (`searchSift`, `ApiError`)
│   │   └── query.ts               Query parser, regex escaping, and URL segment splitter
│   ├── types/              TypeScript definitions
│   │   └── search.ts              Data types for API response (with time_taken), results, and query parser
│   ├── App.css             Application layout and hero-to-results masthead transitions
│   ├── App.tsx             Main application container, pagination state, and search state machine
│   ├── font.css            Font definitions and imports
│   ├── index.css           Global resets and base styles
│   └── main.tsx            React entry point with React Router DOM configuration
├── .dockerignore        Docker build ignore rules
├── Dockerfile           Node/Vite development container definition
├── .env                    Environment configuration
├── .oxlintrc.json          Oxlint linter configuration
├── index.html              HTML entry point template
├── package.json            Dependencies and scripts
├── tsconfig.json           Root TypeScript configuration
└── vite.config.ts          Vite build configuration
```

---

## Getting Started

You can run the frontend using **Docker** or directly with **Node.js & npm**.

---

### Option A: Running with Docker

#### 1. Via Root Docker Compose (Full Stack)

From the project root directory, you can start the frontend alongside the backend and database services:

```bash
# Start just the frontend and its dependencies (backend, mongodb, redis)
docker compose up frontend

# Or run in detached mode
docker compose up -d frontend
```

#### 2. Standalone Frontend Container

To build and run the frontend container independently:

```bash
cd frontend

# Build image
docker build -t sift-frontend .

# Run container (pointing VITE_API_URL to your running backend)
docker run -p 5173:5173 -e VITE_API_URL=http://localhost:8000 sift-frontend
```

Open **[http://localhost:5173](http://localhost:5173)** in your browser.

---

### Option B: Local Development (Node.js & npm)

#### Prerequisites

- **Node.js**: v18.0.0 or higher (v20+ recommended)
- **npm**: v9.0.0 or higher
- **Sift API**: Running locally at `http://localhost:8000` (see root [README.md](../README.md))

#### 1. Install Dependencies

Navigate into the `frontend` folder and install packages:

```bash
cd frontend
npm install
```

#### 2. Configure Environment Variables

The frontend reads configuration from `.env`:

```env
VITE_API_URL=http://localhost:8000
```

> **Note**: Ensure the Sift FastAPI server is running with CORS enabled for `http://localhost:5173` and `http://127.0.0.1:5173` (configured by default in `app.py`).

#### 3. Start the Development Server

```bash
npm run dev
```

The application will be available at:
**[http://localhost:5173](http://localhost:5173)**

---

## Available Scripts

| Command | Description |
|---|---|
| `npm run dev` | Starts the Vite development server with Hot Module Replacement (HMR). |
| `npm run build` | Type-checks with `tsc` and compiles the production bundle into `dist/`. |
| `npm run preview` | Locally serves the production build for testing. |
| `npm run lint` | Runs `oxlint` to lint TypeScript and TSX files. |

---

## API & Data Models

The frontend communicates with the Sift API endpoint `GET /search?q={query}&page={page}`.

### `SearchResult`
```typescript
export type SearchResult = {
  title: string
  url: string
  snippet: string
  score: number
}
```

### `SearchResponse`
```typescript
export type SearchResponse = {
  query: string
  count: number
  total: number
  page: number
  page_size: number
  time_taken?: number
  results: SearchResult[]
}
```

### `ApiError`
Custom error structure used by `searchSift` to carry HTTP status and rate-limiting metadata:
```typescript
export class ApiError extends Error {
  status: number
  retryAfter?: number
}
```

### `Status`
Tracks the UI state lifecycle:
- `'idle'`: Initial state showing the centered home hero view.
- `'loading'`: A query or page transition has been dispatched; displays `<SkeletonList />`.
- `'done'`: Response received; displays result count, query latency (`time_taken`), `<SearchResultItem />` list, and `<Pagination />`.
- `'error'`: An error occurred; displays user-friendly error notices or triggers dedicated full-page error components (`<TooManyRequests />` for HTTP 429, `<ServiceUnavailable />` for HTTP 503).

---

## Supported Query Operators in UI

The client-side parser in `src/lib/query.ts` recognizes standard Sift operators to compute highlighting terms and filter tokens:

| Operator | Syntax Example | Client Handling |
|---|---|---|
| **Phrases** | `"machine learning"` | Extracted as exact phrase token for snippet & title highlighting |
| **Exclusions** | `-spam` | Filtered out of highlight targets |
| **Title match** | `intitle:python` | Extracted as priority highlight term |
| **URL match** | `inurl:wiki` | Passed to backend search engine |
| **Domain filter** | `site:github.com` | Passed to backend search engine |
| **Related terms** | `related:search` | Passed to backend search engine |
