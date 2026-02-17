from research_tools import web_search, extract_article

urls = web_search("latest advances in quantum computing", 3)

print("URLs:", urls)

for u in urls:
    title, text = extract_article(u)
    print("\nTITLE:", title)
    print("TEXT SAMPLE:", text[:500])