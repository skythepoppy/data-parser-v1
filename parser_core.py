from fetchers.html_fetcher import fetch_html
from extractors.html_extractor import extract_article
from cleaners.text_cleaner import clean_text
from output.writer import write_jsonl

def process_url(url):
    html = fetch_html(url)
    if not html:
        return None

    article = extract_article(html)
    article["content"] = clean_text(article["content"])
    article["url"] = url
    return article
