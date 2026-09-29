from bs4 import BeautifulSoup

def results(ranked_results, pages):
    if not ranked_results:
        print("No results found.")
        return

    for url, score in ranked_results:
        html = pages[url]
        soup = BeautifulSoup(html, 'html.parser')
        if soup.title:
            title = soup.title.string
        else:
            title = "No title"
        print(title)
        print(url)
        print("\n")
