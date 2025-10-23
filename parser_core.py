from typing import Optional, Dict, Any
from fetchers.html_fetcher import fetch_html
from extractors.html_extractor import extract_article
from cleaners.text_cleaner import clean_text
from utils.logger import logger

def process_url(url: str) -> Optional[Dict[str, Any]]:

    if not url or not isinstance(url, str):
        logger.error("process_url: invalid url input: %r", url)
        return None

    # Fetch
    try:
        html = fetch_html(url)
    except Exception as exc:
        logger.exception("process_url: unexpected error during fetch for %s", url)
        return None

    if not html:
        logger.info("process_url: no html returned for %s", url)
        return None

    # Extract
    try:
        article = extract_article(html)
    except Exception:
        logger.exception("process_url: extractor raised for %s", url)
        return None

    if not isinstance(article, dict):
        logger.error("process_url: extractor returned non-dict for %s: %r", url, article)
        return None

    content = article.get("content")
  
    if content is None or (isinstance(content, str) and content.strip().lower() == "none") or not str(content).strip():
        logger.info("process_url: empty/missing content for %s", url)
        return None

   
    try:
        article["content"] = clean_text(str(content))
    except Exception:
        logger.exception("process_url: cleaner raised for %s", url)
        return None

    article["url"] = url
    return article