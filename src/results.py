from rich import print

def generate_snippet(document, query_terms):
    content = document.text
    tokens = content.split()
    snippet_length = 20
    for term in query_terms:
        try:
            index = tokens.index(term)
            start = max(0, index - snippet_length // 2)
            end = min(len(tokens), index + snippet_length // 2)
            return " ".join(tokens[start:end])
        except ValueError:
            continue
    return " ".join(tokens[:snippet_length]) + "..."

def results(ranked_results, pages, query_terms):
    if not ranked_results:
        print("No results found.")
        return

    for url, score in ranked_results:
        doc = pages[url]
        snippet = generate_snippet(doc, query_terms)
        print(f"[link={doc.url}][bold blue]{doc.title}[/bold blue][/link]")
        print(snippet)
        print("\n")
