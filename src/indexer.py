from tokenizer import tokenize
from stemmer import stem
from schemas.search_index import TermDocument, IndexStats, Posting
from schemas.page import Page
from pymongo import UpdateOne

async def index_page(page: Page):
    url = page.url
    words = stem(tokenize(page.clean_text))
    doc_length = len(words)
    term_positions = {}
    
    for position, word in enumerate(words):
        if word not in term_positions:
            term_positions[word] = []
        term_positions[word].append(position)
    
    stats = await IndexStats.find_one(IndexStats.id_name == "global_stats")
    if not stats:
        stats = IndexStats(
            document_length={},
            avg_document_length=0.0,
            total_documents=0
        )
        await stats.insert()
    
    is_new_page = url not in stats.document_length
    
    if not is_new_page:
        return
    stats.document_length[url] = doc_length
    stats.total_documents += 1
    total_words = sum(stats.document_length.values())
    stats.avg_document_length = total_words / stats.total_documents
    await stats.save()

    bulk_ops = []
    for word, positions in term_positions.items():
        tf = len(positions)
        posting_doc = Posting(url=url, tf=tf, positions=positions).model_dump()
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
        collection = TermDocument.get_pymongo_collection()
        await collection.bulk_write(bulk_ops, ordered=False)