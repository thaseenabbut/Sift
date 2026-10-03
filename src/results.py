from rich import print
import re

def generate_snippet(document, query_terms, term_positions):
    content = document.text
    tokens = content.split()
    best_index = None
    snippet_length = 20
    
    for term in query_terms:
        positions = term_positions.get(term.stemmed)
        if positions:
            best_index = positions[0]
            break
        
    if best_index is None:
        return " ".join(tokens[:snippet_length]) + "..."
        
    start = max(0, best_index - snippet_length // 2)
    end = min(len(tokens), best_index + snippet_length // 2)
    
    suffix = "..." if end < len(tokens) else ""
    
    return " ".join(tokens[start:end]) + suffix

def highlighting_terms(snippet, query_terms):
    highlighted = snippet
    for term in query_terms:
        term = term.original
        highlighted = re.sub(
            rf"(?i)({re.escape(term)})",
            r"[bold red]\1[/bold red]",
            highlighted
        )
    return highlighted

def results(ranked_results, pages, query_terms, search_index):
    if not ranked_results:
        print("Your search did not match any documents. Please try different keywords.")
        return

    for url, score in ranked_results:
        doc = pages[url]
        positions = {
            query.stemmed: search_index.inverted_index[query.stemmed][url]["positions"]
            for query in query_terms
            if query.stemmed in search_index.inverted_index  and url in search_index.inverted_index[query.stemmed]
        }
        snippet = generate_snippet(doc, query_terms, positions)
        highlighted_snippet = highlighting_terms(snippet, query_terms)
        print(f"[link={doc.url}][bold blue]{doc.title}[/bold blue][/link]")
        print(f"[dim]{highlighted_snippet}[/dim]")
        print("\n")