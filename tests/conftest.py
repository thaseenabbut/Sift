"""
Shared fixtures for the Sift API test suite.

Key design decision:
  • We import `app` from app.py but override its lifespan so the tests
    never actually connect to MongoDB.
  • Every test that needs to control search results patches `src.api.routes.search`
    via the `mock_search` fixture.
"""

import pytest
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app import app


# ---------------------------------------------------------------------------
# Override the lifespan so tests skip the real MongoDB connect/disconnect
# ---------------------------------------------------------------------------

@asynccontextmanager
async def _noop_lifespan(application: FastAPI):
    """No-op lifespan – avoids hitting a real database."""
    yield


app.router.lifespan_context = _noop_lifespan


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_search():
    """
    Yields an ``AsyncMock`` that replaces ``src.api.routes.search``.

    Usage in tests::

        mock_search.return_value = [{"title": "T", "url": "http://…", …}]
        response = await client.get("/search", params={"q": "python"})
    """
    with patch("src.api.routes.search", new_callable=AsyncMock) as m:
        yield m


@pytest.fixture()
async def client():
    """
    Async HTTP client bound to the Sift app.

    Uses ``httpx.AsyncClient`` with ``ASGITransport`` – the recommended
    approach for testing async FastAPI apps.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
