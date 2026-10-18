from dataclasses import dataclass, field
import logging
import math
from typing import Any

from indexer import ensure_stats, index_page, refresh_stat_totals
from schemas.page import Page
from schemas.search_index import IndexStats, TermDocument
from stemmer import stem
from tokenizer import tokenize

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IntegrityIssue:
    code: str
    message: str
    url: str | None = None
    term: str | None = None


@dataclass
class IntegrityReport:
    issues: list[IntegrityIssue] = field(default_factory=list)

    @property
    def is_healthy(self) -> bool:
        return not self.issues

    def by_code(self, code: str) -> list[IntegrityIssue]:
        return [issue for issue in self.issues if issue.code == code]


@dataclass
class RepairResult:
    actions: list[str]
    report: IntegrityReport


def _add(report: IntegrityReport, code: str, message: str, *, url=None, term=None):
    report.issues.append(IntegrityIssue(code, message, url=url, term=term))


def _valid_length(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _valid_posting(posting: Any) -> bool:
    url = getattr(posting, "url", None)
    tf = getattr(posting, "tf", None)
    positions = getattr(posting, "positions", None)
    return (
        isinstance(url, str)
        and bool(url)
        and isinstance(tf, int)
        and not isinstance(tf, bool)
        and tf > 0
        and isinstance(positions, list)
        and len(positions) == tf
        and all(isinstance(position, int) and not isinstance(position, bool) and position >= 0 for position in positions)
        and positions == sorted(set(positions))
    )


def inspect_index_state(pages, terms, stats) -> IntegrityReport:
    report = IntegrityReport()
    pages = list(pages)
    terms = list(terms)
    page_urls = [getattr(page, "url", None) for page in pages]
    valid_page_urls = {url for url in page_urls if isinstance(url, str) and url}

    for url in valid_page_urls:
        if page_urls.count(url) > 1:
            _add(report, "duplicate_page_url", "More than one Page has this URL.", url=url)

    if stats is None:
        if pages or terms:
            _add(report, "missing_stats", "Indexed data exists but global statistics are missing.")
        return report

    lengths = getattr(stats, "document_length", None)
    if not isinstance(lengths, dict):
        _add(report, "invalid_document_length_map", "document_length is not a mapping.")
        return report

    for url in valid_page_urls:
        if url not in lengths:
            _add(report, "page_missing_document_length", "Page has no document-length entry.", url=url)

    for url, length in lengths.items():
        if url not in valid_page_urls:
            _add(report, "orphan_document_length", "document_length has no corresponding Page.", url=url)
        if not _valid_length(length):
            _add(report, "invalid_document_length", "Document length must be a non-negative integer.", url=url)

    tf_by_url = {}
    for term_document in terms:
        term = getattr(term_document, "term", None)
        postings = getattr(term_document, "postings", None)
        if not isinstance(postings, list):
            _add(report, "invalid_postings", "Term postings are not a list.", term=term)
            continue
        if not postings:
            _add(report, "empty_term_document", "Term document has no postings.", term=term)
        if getattr(term_document, "document_frequency", None) != len(postings):
            _add(report, "incorrect_document_frequency", "document_frequency does not match stored postings.", term=term)

        seen_urls = set()
        for posting in postings:
            url = getattr(posting, "url", None)
            if not _valid_posting(posting):
                _add(report, "invalid_posting", "Posting has invalid URL, tf, or positions.", url=url, term=term)
                continue
            if url in seen_urls:
                _add(report, "duplicate_posting_url", "Term has more than one posting for this URL.", url=url, term=term)
            seen_urls.add(url)
            if url not in valid_page_urls:
                _add(report, "orphan_posting", "Posting has no corresponding Page.", url=url, term=term)
            else:
                tf_by_url[url] = tf_by_url.get(url, 0) + posting.tf

    for page in pages:
        url = getattr(page, "url", None)
        if url not in lengths or not _valid_length(lengths.get(url)):
            continue
        try:
            expected_length = len(stem(tokenize(page.clean_text)))
        except (AttributeError, TypeError):
            _add(report, "unreadable_page_text", "Page text cannot be tokenized.", url=url)
            continue
        if lengths[url] != expected_length:
            _add(report, "document_length_content_mismatch", "Length disagrees with the stored page text.", url=url)
        if tf_by_url.get(url, 0) != lengths[url]:
            _add(report, "document_length_posting_mismatch", "Posting tf total disagrees with document length.", url=url)

    expected_total = len(lengths)
    if getattr(stats, "total_documents", None) != expected_total:
        _add(report, "incorrect_total_documents", "total_documents does not match document_length.")

    if all(_valid_length(length) for length in lengths.values()):
        expected_average = sum(lengths.values()) / expected_total if expected_total else 0.0
        actual_average = getattr(stats, "avg_document_length", None)
        if not isinstance(actual_average, (int, float)) or not math.isfinite(actual_average) or not math.isclose(actual_average, expected_average):
            _add(report, "incorrect_avg_document_length", "avg_document_length does not match document_length.")
    return report


async def _load_index_state():
    pages = await Page.find_all().to_list()
    terms = await TermDocument.find_all().to_list()
    stats = await IndexStats.find_one({"id_name": "global_stats"})
    return pages, terms, stats


async def check_index_integrity() -> IntegrityReport:
    return inspect_index_state(*await _load_index_state())


async def repair_index_integrity(*, rebuild_pages: bool = False) -> RepairResult:
    pages, terms, stats = await _load_index_state()
    page_urls = {page.url for page in pages}
    actions = []

    for term_document in terms:
        postings = list(getattr(term_document, "postings", []))
        safe_postings = [
            posting for posting in postings
            if _valid_posting(posting) and posting.url in page_urls
        ]
        if not safe_postings:
            await term_document.delete()
            actions.append(f"removed empty/orphan term: {term_document.term}")
            continue
        changed = safe_postings != postings
        if changed:
            term_document.postings = safe_postings
            actions.append(f"removed orphan/invalid postings: {term_document.term}")
        if term_document.document_frequency != len(safe_postings):
            term_document.document_frequency = len(safe_postings)
            changed = True
            actions.append(f"recalculated document frequency: {term_document.term}")
        if changed:
            await term_document.save()

    if stats is None and (pages or terms):
        stats = await ensure_stats()
        actions.append("created missing global statistics")

    if stats is not None:
        orphan_urls = set(stats.document_length) - page_urls
        invalid_urls = {
            url for url, length in stats.document_length.items()
            if not _valid_length(length)
        }
        stale_urls = orphan_urls | invalid_urls
        if stale_urls:
            for url in stale_urls:
                del stats.document_length[url]
            if orphan_urls:
                actions.append("removed orphan document-length entries")
            if invalid_urls:
                actions.append("removed invalid document-length entries")

        before = (stats.total_documents, stats.avg_document_length)
        refresh_stat_totals(stats)
        if before != (stats.total_documents, stats.avg_document_length) or stale_urls:
            await stats.save()
            actions.append("recalculated global statistics")

    if rebuild_pages:
        if stats is None:
            stats = await ensure_stats()
        failed = []
        for page in pages:
            try:
                await index_page(page)
            except Exception:
                logger.warning("Failed to re-index page: %s", page.url)
                failed.append(page.url)
        if failed:
            actions.append(f"failed to rebuild {len(failed)} page(s)")
        actions.append("rebuilt postings and lengths from stored Page text")

    return RepairResult(actions=actions, report=await check_index_integrity())
