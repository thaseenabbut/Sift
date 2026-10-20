# Sift Frontend

A fast, responsive, and minimalist web search interface for the **Sift** search engine, built with **React 19**, **TypeScript**, and **Vite**.

---

## Overview

The Sift frontend connects to the Sift FastAPI backend to deliver a Google-like search experience. It features a clean dual-mode interface (hero homepage transitioning into a focused results layout), instant client-side query term highlighting, smart breadcrumb URL parsing, domain favicon fetching, skeleton loading states, and race-condition-safe request dispatching.

## Features

- **Dual-State Interface**: Clean, centered hero landing view that smoothly transitions into a sticky top masthead with results upon search submission.
- **Client-Side Query Parsing & Highlighting**: Automatically extracts quoted phrases, normal terms, and operators (e.g. `intitle:`) to dynamically highlight matching text in result titles and snippets using `<mark>`.
- **URL & Breadcrumb Parsing**: Parses result URLs to extract the clean site name, domain origin, and path breadcrumbs (`example.com › docs › api`).
- **Favicon Resolution**: Fetches high-resolution site favicons dynamically, with automatic graceful hiding on load failure.
- **Race Condition Prevention**: Employs monotonic request IDs (`requestId.current`) to discard outdated, slower responses when rapid successive queries are submitted.
- **Accessible & Semantic UX**: Includes proper ARIA attributes (`role="search"`, `aria-busy`, `aria-live="polite"`), animated skeleton placeholders during loading, and clear empty/error states.
- **Dynamic Document Title**: Updates browser tab title to reflect the active search query (`{query} - Sift Search`).

---

## Tech Stack

| Technology | Purpose |
|---|---|
| **[React 19](https://react.dev/)** | Core UI library |
| **[TypeScript](https://www.typescriptlang.org/)** | Static type checking and safety |
| **[Vite 8](https://vite.dev/)** | Lightning-fast build tool and local dev server |
| **[Oxlint](https://oxc.rs/)** | High-performance JavaScript/TypeScript linter |
| **Vanilla CSS** | Custom responsive design system, typography, and micro-animations |

---

## Directory Structure

```text
frontend/
├── public/                 Static public assets (favicons, icons)
├── src/
│   ├── assets/             Frontend assets
│   ├── components/         Reusable React components
│   │   ├── SearchBar.tsx          Search input form with SVG search icon
│   │   ├── SearchResultItem.tsx   Individual result card with favicon, title, snippet, and highlights
│   │   └── SearchResults.tsx      Results list container, skeleton loader, and status messages
│   ├── lib/                Utility and helper functions
│   │   ├── api.ts                 Backend API client (`searchSift`)
│   │   └── query.ts               Query parser, regex escaping, and URL segment splitter
│   ├── types/              TypeScript definitions
│   │   └── search.ts              Data types for API response, results, and query parser
│   ├── App.css             Application layout, masthead transitions, and responsive styling
│   ├── App.tsx             Main application container and search state machine
│   ├── font.css            Font definitions and imports
│   ├── index.css           Global resets and base styles
│   └── main.tsx            React entry point (mounts to DOM)
├── .env                    Environment configuration
├── .oxlintrc.json          Oxlint linter configuration
├── index.html              HTML entry point template
├── package.json            Dependencies and scripts
├── tsconfig.json           Root TypeScript configuration
└── vite.config.ts          Vite build configuration
```

---

## Getting Started

### Prerequisites

- **Node.js**: v18.0.0 or higher (v20+ recommended)
- **npm**: v9.0.0 or higher
- **Sift API**: Running locally at `http://127.0.0.1:8000` (see root [README.md](../README.md))

### 1. Install Dependencies

Navigate into the `frontend` folder and install packages:

```bash
cd frontend
npm install
```

### 2. Configure Environment Variables

The frontend is configured via `.env`:

```env
PUBLIC_SIFT_API_URL=http://127.0.0.1:8000
```

> **Note**: Ensure the Sift FastAPI server is running with CORS enabled for `http://localhost:5173` and `http://127.0.0.1:5173` (configured by default in `app.py`).

### 3. Start the Development Server

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

The frontend communicates with the Sift API endpoint `GET /search?q={query}`.

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
  results: SearchResult[]
}
```

### `Status`
Tracks the UI state lifecycle:
- `'idle'`: Initial state showing the centered home hero view.
- `'loading'`: A query has been dispatched; displays `<SkeletonList />`.
- `'done'`: Response received; displays result count and `<SearchResultItem />` list.
- `'error'`: An error occurred; displays user-friendly error notice.

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
