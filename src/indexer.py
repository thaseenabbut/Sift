from tokenizer import tokenize
from stemmer import stem
from schemas.search_index import TermDocument, IndexStats, Posting
from schemas.page import Page
from pymongo import UpdateOne

async def _ensure_stats():
    stats = await IndexStats.find_one(IndexStats.id_name == "global_stats")
    if stats:
        return stats
    stats = IndexStats(
        document_length={},
        avg_document_length=0.0,
        total_documents=0,
    )
    await stats.insert()
    return stats


async def _remove_page_postings(collection, url: str):
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
            {
                "$set": {
                    "document_frequency": {"$size": "$postings"}
                }
            },
        ],
    )
    await collection.delete_many({"postings": {"$size": 0}})


async def index_page(page: Page):
    url = page.url
    words = stem(tokenize(page.clean_text))
    doc_length = len(words)
    term_positions = {}

    for position, word in enumerate(words):
        if word not in term_positions:
            term_positions[word] = []
        term_positions[word].append(position)

    stats = await _ensure_stats()
    is_new_page = url not in stats.document_length
    collection = TermDocument.get_pymongo_collection()

    await _remove_page_postings(collection, url)

    bulk_ops = []
    for word, positions in term_positions.items():
        posting_doc = Posting(
            url=url,
            tf=len(positions),
            positions=positions,
        ).model_dump()

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
                    {
                        "$set": {
                            "document_frequency": {"$size": "$postings"}
                        }
                    },
                ],
                upsert=True,
            )
        )

    if bulk_ops:
        await collection.bulk_write(bulk_ops, ordered=False)

    if is_new_page:
        stats.total_documents += 1

    stats.document_length[url] = doc_length
    stats.total_documents = len(stats.document_length)
    total_words = sum(stats.document_length.values())
    stats.avg_document_length = (
        total_words / stats.total_documents if stats.total_documents else 0.0
    )

    await stats.save()
