def results(ranked_results, pages):
    if not ranked_results:
        print("No results found.")
        return

    for url, score in ranked_results:
        doc = pages[url]
        print(doc.title)
        print(doc.url)
        print("\n")
