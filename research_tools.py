from duckduckgo_search import DDGS

def web_search(query, k=5):
    out = []
    with DDGS() as d:
        for r in d.text(query, max_results=k):
            out.append(f"{r['title']} — {r['body']}")
    return out