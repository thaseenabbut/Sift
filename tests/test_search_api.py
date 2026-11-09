"""
Automated tests for the Sift search API (/search endpoint).

Organised into four sections:

1. **Success tests**   – happy-path: correct fields, counts, limits.
2. **Validation tests** – bad inputs return the right status codes.
3. **Failure tests**   – simulated DB errors, missing indexes, and unexpected exceptions.
4. **Regression tests** – guard specific contract details against accidental breakage.
"""

import pytest
from pymongo.errors import PyMongoError


# ═══════════════════════════════════════════════════════════════════════════
# Helper factories
# ═══════════════════════════════════════════════════════════════════════════

def _make_result(
    title: str = "Example Page",
    url: str = "https://example.com",
    snippet: str = "An example snippet for testing.",
    score: float = 4.2,
) -> dict:
    """Build a single search-result dict matching the SearchResult schema."""
    return {"title": title, "url": url, "snippet": snippet, "score": score}


def _make_results(n: int) -> list[dict]:
    """Build *n* unique search-result dicts."""
    return [
        _make_result(
            title=f"Page {i}",
            url=f"https://example.com/{i}",
            snippet=f"Snippet for result {i}.",
            score=round(10 - i * 0.1, 2),
        )
        for i in range(1, n + 1)
    ]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Success tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSearchSuccess:
    """Verify correct behaviour when the search function returns normally."""

    @pytest.mark.anyio
    async def test_returns_200_with_results(self, client, mock_search):
        """Basic request: 200 status and the expected response shape."""
        mock_search.return_value = [_make_result()]
        resp = await client.get("/search", params={"q": "python"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["query"] == "python"
        assert body["count"] == 1
        assert len(body["results"]) == 1

    @pytest.mark.anyio
    async def test_result_fields(self, client, mock_search):
        """Each result contains exactly the documented fields."""
        mock_search.return_value = [_make_result()]
        resp = await client.get("/search", params={"q": "fastapi"})

        result = resp.json()["results"][0]
        assert set(result.keys()) == {"title", "url", "snippet", "score"}
        assert isinstance(result["title"], str)
        assert isinstance(result["url"], str)
        assert isinstance(result["snippet"], str)
        assert isinstance(result["score"], float)

    @pytest.mark.anyio
    async def test_empty_results(self, client, mock_search):
        """A query that matches nothing still returns 200 with count 0."""
        mock_search.return_value = []
        resp = await client.get("/search", params={"q": "xyznonexistent"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 0
        assert body["results"] == []

    @pytest.mark.anyio
    async def test_default_limit(self, client, mock_search):
        """Without an explicit limit, at most 10 results are returned."""
        mock_search.return_value = _make_results(25)
        resp = await client.get("/search", params={"q": "python"})

        body = resp.json()
        assert body["count"] == 10
        assert len(body["results"]) == 10

    @pytest.mark.anyio
    async def test_custom_limit(self, client, mock_search):
        """An explicit limit truncates the result list accordingly."""
        mock_search.return_value = _make_results(25)
        resp = await client.get("/search", params={"q": "python", "limit": 5})

        body = resp.json()
        assert body["count"] == 5
        assert len(body["results"]) == 5

    @pytest.mark.anyio
    async def test_limit_larger_than_results(self, client, mock_search):
        """A limit larger than the actual result count returns all results."""
        mock_search.return_value = _make_results(3)
        resp = await client.get("/search", params={"q": "python", "limit": 50})

        body = resp.json()
        assert body["count"] == 3

    @pytest.mark.anyio
    async def test_query_is_stripped(self, client, mock_search):
        """Leading/trailing whitespace is stripped from the query."""
        mock_search.return_value = [_make_result()]
        resp = await client.get("/search", params={"q": "  python  "})

        body = resp.json()
        assert body["query"] == "python"

    @pytest.mark.anyio
    async def test_max_limit(self, client, mock_search):
        """Limit=100 (the documented maximum) is accepted."""
        mock_search.return_value = _make_results(100)
        resp = await client.get("/search", params={"q": "python", "limit": 100})

        assert resp.status_code == 200
        assert resp.json()["count"] == 100


# ═══════════════════════════════════════════════════════════════════════════
# 2. Validation tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSearchValidation:
    """Verify that invalid inputs are rejected with proper status codes."""

    @pytest.mark.anyio
    async def test_missing_query(self, client):
        """Omitting `q` entirely returns 422."""
        resp = await client.get("/search")
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_empty_query(self, client):
        """An empty-string query returns 422 (min_length=1)."""
        resp = await client.get("/search", params={"q": ""})
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_whitespace_only_query(self, client, mock_search):
        """A query consisting only of spaces returns 400 after strip()."""
        # The route strips the query, then checks `if not query`.
        # Need mock_search fixture so the patch is in place (even though
        # it shouldn't be reached).
        resp = await client.get("/search", params={"q": "   "})
        assert resp.status_code == 400
        assert "empty" in resp.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_limit_zero(self, client):
        """limit=0 is below the minimum (ge=1) → 422."""
        resp = await client.get("/search", params={"q": "python", "limit": 0})
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_limit_negative(self, client):
        """Negative limit → 422."""
        resp = await client.get("/search", params={"q": "python", "limit": -5})
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_limit_exceeds_maximum(self, client):
        """limit=101 exceeds the maximum (le=100) → 422."""
        resp = await client.get("/search", params={"q": "python", "limit": 101})
        assert resp.status_code == 422

    @pytest.mark.anyio
    async def test_limit_non_integer(self, client):
        """A non-integer limit → 422."""
        resp = await client.get("/search", params={"q": "python", "limit": "abc"})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════
# 3. Failure tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSearchFailures:
    """Simulate back-end failures and verify the API responds gracefully."""

    @pytest.mark.anyio
    async def test_missing_search_index(self, client, mock_search):
        """When the search function returns None (no index), expect 503."""
        mock_search.return_value = None
        resp = await client.get("/search", params={"q": "python"})

        assert resp.status_code == 503
        assert "index" in resp.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_database_error(self, client, mock_search):
        """A PyMongoError from the search layer surfaces as 503."""
        mock_search.side_effect = PyMongoError("connection lost")
        resp = await client.get("/search", params={"q": "python"})

        assert resp.status_code == 503
        assert "unavailable" in resp.json()["detail"].lower()

    @pytest.mark.anyio
    async def test_unexpected_exception(self, client, mock_search):
        """Any other exception surfaces as 500."""
        mock_search.side_effect = RuntimeError("something broke")
        resp = await client.get("/search", params={"q": "python"})

        assert resp.status_code == 500
        assert "unexpected" in resp.json()["detail"].lower()


# ═══════════════════════════════════════════════════════════════════════════
# 4. Regression tests
# ═══════════════════════════════════════════════════════════════════════════

class TestSearchRegression:
    """Guard specific API contract details against accidental breakage."""

    @pytest.mark.anyio
    async def test_response_content_type(self, client, mock_search):
        """The endpoint always returns application/json."""
        mock_search.return_value = [_make_result()]
        resp = await client.get("/search", params={"q": "python"})
        assert "application/json" in resp.headers["content-type"]

    @pytest.mark.anyio
    async def test_query_echoed_back(self, client, mock_search):
        """The response body always echoes the (stripped) query."""
        mock_search.return_value = []
        resp = await client.get("/search", params={"q": "  machine learning  "})
        assert resp.json()["query"] == "machine learning"

    @pytest.mark.anyio
    async def test_results_order_preserved(self, client, mock_search):
        """Results appear in the same order returned by the search function."""
        ordered = _make_results(5)
        mock_search.return_value = ordered
        resp = await client.get("/search", params={"q": "python", "limit": 5})

        returned_titles = [r["title"] for r in resp.json()["results"]]
        expected_titles = [r["title"] for r in ordered]
        assert returned_titles == expected_titles

    @pytest.mark.anyio
    async def test_count_matches_results_length(self, client, mock_search):
        """The `count` field always equals `len(results)` in the response."""
        mock_search.return_value = _make_results(7)
        resp = await client.get("/search", params={"q": "python", "limit": 5})

        body = resp.json()
        assert body["count"] == len(body["results"])

    @pytest.mark.anyio
    async def test_database_error_does_not_leak_internals(self, client, mock_search):
        """A DB error's detail message must not expose internal stack traces."""
        mock_search.side_effect = PyMongoError("secret connection string")
        resp = await client.get("/search", params={"q": "python"})

        detail = resp.json()["detail"]
        assert "secret" not in detail
        assert "connection string" not in detail

    @pytest.mark.anyio
    async def test_unexpected_error_does_not_leak_internals(self, client, mock_search):
        """An unexpected error's detail must not expose internal details."""
        mock_search.side_effect = ValueError("internal state corruption")
        resp = await client.get("/search", params={"q": "python"})

        detail = resp.json()["detail"]
        assert "internal state" not in detail

    @pytest.mark.anyio
    async def test_search_called_with_stripped_query(self, client, mock_search):
        """The search function receives the *stripped* query, not raw input."""
        mock_search.return_value = []
        await client.get("/search", params={"q": "  hello world  "})

        mock_search.assert_awaited_once()
        actual_query = mock_search.call_args[0][0]
        assert actual_query == "hello world"

    @pytest.mark.anyio
    async def test_get_method_only(self, client, mock_search):
        """The /search endpoint only accepts GET. POST returns 405."""
        mock_search.return_value = []
        resp = await client.post("/search", params={"q": "python"})
        assert resp.status_code == 405
