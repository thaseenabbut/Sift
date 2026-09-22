# Sift

Sift is a small, modular Python search-engine project. It is structured as a
pipeline that crawls documents, extracts and tokenizes their contents, builds
an index, ranks matching documents, and returns search results.

## Project structure

```text
main.py             Application entry point
src/
  crawler.py        Document discovery and retrieval
  parser.py         Content extraction
  tokenizer.py      Text normalization and tokenization
  indexer.py        Search-index construction and persistence
  ranker.py         Result scoring and ordering
  search.py         Query execution
data/               Local, generated application data
```

## Getting started

Sift targets Python 3.11 or newer.

```bash
git clone <repository-url>
cd Sift
python3 -m venv .venv
source .venv/bin/activate
```

Once the project dependencies and command-line interface are in place, run the
application from the repository root:

```bash
python main.py
```

## Development

Keep reusable application logic in `src/` and use `main.py` only to wire the
command-line interface to that logic. Generated indexes, crawler caches, and
downloaded documents belong under `data/` and are intentionally excluded from
version control.

## License

Sift is released under the [MIT License](LICENSE).
