from datetime import datetime, timezone
from typing import Union

from pymongo import UpdateOne

from tokenizer import tokenize
from stemmer import stem
from schemas.search_index import TermDocument, IndexStats, Posting
from schemas.page import Page


async def ensure_stats():
    stats = await IndexStats.find_one({"id_name": "global_stats"})
    if stats:
        return stats
    stats = IndexStats(
        document_length={},
        avg_document_length=0.0,
        total_documents=0
    )
    await stats.insert()
    return stats


def refresh_stat_totals(stats: IndexStats) -> None:
    stats.total_documents = len(stats.document_length)
    stats.avg_document_length = (
        sum(stats.document_length.values()) / stats.total_documents
        if stats.total_documents
        else 0.0
    )


async def remove_page_postings(collection, url: str):
    await collection.update_many(
        {},
        [
            {
                "$set": {
                    "postings": {
                        "$filter": {
                            "input": {"$ifNull": ["$postings", []]},
                            "as": "posting",
                            "cond": {"$ne": ["$$posting.url", url]},
                        }
                    }
                }
            },
            {"$set": {"document_frequency": {"$size": "$postings"}}},
        ],
    )
    await collection.delete_many({"postings": {"$size": 0}})


async def remove_document_from_index(url: str, delete_page: bool = False) -> bool:
    collection = TermDocument.get_pymongo_collection()
    await remove_page_postings(collection, url)

    stats = await IndexStats.find_one({"id_name": "global_stats"})
    removed = False
    if stats is not None and url in stats.document_length:
        del stats.document_length[url]
        refresh_stat_totals(stats)
        await stats.save()
        removed = True

    if delete_page:
        page = await Page.find_one({"url": url})
        if page is not None:
            await page.delete()
            removed = True
    return removed


async def migrate_page_url(old_url: str, new_url: Union[str, Page], new_hash: str | None = None) -> bool:
    destination_url = new_url.url if isinstance(new_url, Page) else new_url
    if old_url == destination_url:
        return False

    source = await Page.find_one({"url": old_url})
    destination = await Page.find_one({"url": destination_url})

    if destination is not None and source is not None:
        return False
    if source is not None and new_hash is not None and source.content_hash != new_hash:
        return False
    if source is not None and destination is None:
        destination = source
    if destination is None:
        return False

    stats = await IndexStats.find_one({"id_name": "global_stats"})
    if stats is None or old_url not in stats.document_length:
        return False
    if destination_url in stats.document_length and destination_url != old_url:
        return False

    collection = TermDocument.get_pymongo_collection()
    await collection.update_many(
        {"postings.url": old_url},
        [
            {
                "$set": {
                    "postings": {
                        "$reduce": {
                            "input": {
                                "$map": {
                                    "input": {"$ifNull": ["$postings", []]},
                                    "as": "posting",
                                    "in": {
                                        "$cond": [
                                            {"$eq": ["$$posting.url", old_url]},
                                            {"$mergeObjects": ["$$posting", {"url": destination_url}]},
                                            "$$posting",
                                        ]
                                    },
                                }
                            },
                            "initialValue": [],
                            "in": {
                                "$cond": [
                                    {
                                        "$in": [
                                            "$$this.url",
                                            {
                                                "$map": {
                                                    "input": "$$value",
                                                    "as": "existing",
                                                    "in": "$$existing.url",
                                                }
                                            },
                                        ]
                                    },
                                    "$$value",
                                    {"$concatArrays": ["$$value", ["$$this"]]},
                                ]
                            },
                        }
                    },
                }
            },
            {"$set": {"document_frequency": {"$size": "$postings"}}},
        ],
    )

    if source is not None:
        source.url = destination_url
        source.last_crawled_at = datetime.now(timezone.utc)
        await source.save()

    length = stats.document_length.pop(old_url)
    stats.document_length[destination_url] = length
    refresh_stat_totals(stats)
    await stats.save()
    return True


async def index_page(page: Page):
    url = page.url
    words = stem(tokenize(page.clean_text))
    doc_length = len(words)
    term_positions = {}

    for position, word in enumerate(words):
        term_positions.setdefault(word, []).append(position)

    stats = await ensure_stats()
    collection = TermDocument.get_pymongo_collection()

    # Re-indexing is a replacement, so stale terms cannot survive content
    # changes and repeated calls cannot create duplicate postings.
    await remove_page_postings(collection, url)

    bulk_ops = []
    for word, positions in term_positions.items():
        posting_doc = Posting(url=url, tf=len(positions), positions=positions).model_dump()
        bulk_ops.append(
            UpdateOne(
                {"term": word},
                [
                    {
                        "$set": {
                            "term": {"$ifNull": ["$term", word]},
                            "postings": {
                                "$concatArrays": [
                                    {
                                        "$filter": {
                                            "input": {"$ifNull": ["$postings", []]},
                                            "cond": {"$ne": ["$$this.url", url]},
                                        }
                                    },
                                    [posting_doc],
                                ]
                            },
                        }
                    },
                    {"$set": {"document_frequency": {"$size": "$postings"}}},
                ],
                upsert=True,
            )
        )

    if bulk_ops:
        await collection.bulk_write(bulk_ops, ordered=False)

    stats.document_length[url] = doc_length
    refresh_stat_totals(stats)
    await stats.save()
