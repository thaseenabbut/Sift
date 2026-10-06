from tokenizer import tokenize
from stemmer import stem
from schemas.search_index import TermDocument, IndexStats, Posting
from schemas.page import Page

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
    
    for word, positions in term_positions.items():
        tf = len(positions)
        posting = Posting(tf=tf, positions=positions)
        
        term_doc = await TermDocument.find_one(TermDocument.term == word)
        
        if not term_doc:
            term_doc = TermDocument(
                term=word,
                document_frequency=1,
                postings={url: posting}
            )
            await term_doc.insert()
        else:
            term_doc.document_frequency += 1
            term_doc.postings[url] = posting
            await term_doc.save()