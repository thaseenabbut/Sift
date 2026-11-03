from rich import print
import re

def generate_snippet(document, query_terms, term_positions, snippet_length=20, lead=3):
    tokens = document.clean_text.split()
    if not tokens:
        return ""

    hits = sorted(
        (pos, term.stemmed)
        for term in query_terms
        for pos in term_positions.get(term.stemmed, [])
    )
    if not hits:
        return _render(tokens, 0, snippet_length)
    
    window = snippet_length - lead
    counts = {}
    left = 0
    best_start, best_score = hits[0][0], 0

    for pos, stem in hits:
        counts[stem] = counts.get(stem, 0) + 1
        while pos - hits[left][0] >= window:
            old = hits[left][1]
            counts[old] -= 1
            if counts[old] == 0:
                del counts[old]
            left += 1
        if len(counts) > best_score:
            best_score, best_start = len(counts), hits[left][0]

    start = max(0, best_start - lead)
    start = min(start, max(0, len(tokens) - snippet_length))
    return _render(tokens, start, snippet_length)


def _render(tokens, start, length):
    end = min(len(tokens), start + length)
    prefix = "... " if start > 0 else ""
    suffix = " ..." if end < len(tokens) else ""
    return prefix + " ".join(tokens[start:end]) + suffix

async def highlighting_terms(snippet, query_terms):
    highlighted = snippet
    for term in query_terms:
        term = term.original
        highlighted = re.sub(
            rf"(?i)({re.escape(term)})",
            r"[bold yellow]\1[/bold yellow]",
            highlighted
        )
    return highlighted

async def results(ranked_results, pages, query_terms, term_docs_lookup, result_data):
    if not ranked_results:
        print("Your search did not match any documents. Please try different keywords.")
        return

    for url, score in ranked_results:
        doc = pages[url]
        positions = {
            query.stemmed: term_docs_lookup[query.stemmed].postings_by_url[url].positions
            for query in query_terms
            if query.stemmed in term_docs_lookup and url in term_docs_lookup[query.stemmed].postings_by_url
        }
        snippet = generate_snippet(doc, query_terms, positions, snippet_length=20, lead=3)
        highlighted_snippet = await highlighting_terms(snippet, query_terms)
        print(f"[link={doc.url}][bold blue]{doc.title}[/bold blue][/link]")
        print(f"[dim]{highlighted_snippet}[/dim]")
        print("\n")
        
        result_data.append({
            "title": doc.title,
            "url": doc.url,
            "snippet": snippet,
            "score": score,
        })