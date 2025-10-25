from typing import Optional, Dict, Any
from fetchers.html_fetcher import fetch_html
from extractors.html_extractor import extract_article
from cleaners.text_cleaner import clean_text
from utils.logger import logger


def process_url(url: str, lowercase_content: bool = False) -> Optional[Dict[str, Any]]:
 

    if not url or not isinstance(url, str):
        logger.error("process_url: invalid url input: %r", url)
        return None

    # fetch
    try:
        html = fetch_html(url)
    except Exception as exc:
        logger.exception("process_url: unexpected error during fetch for %s", url)
        return None

    if not html:
        logger.warning("process_url: no HTML returned for %s", url)
        return None

    # Extract
    try:
        article = extract_article(html)
    except Exception:
        logger.exception("process_url: extractor raised an exception for %s", url)
        return None

    if not isinstance(article, dict):
        logger.error("process_url: extractor returned non-dict for %s: %r", url, article)
        return None

    # Clean content
    content = article.get("content")
    if not content or str(content).strip().lower() in ["none", ""]:
        logger.warning("process_url: empty/missing content for %s", url)
       
        article["content"] = "No content available"
    else:
        try:
            article["content"] = clean_text(str(content), lowercase=lowercase_content)
        except Exception:
            logger.exception("process_url: cleaner raised an exception for %s", url)
            return None

    # title exists 
    if not article.get("title"):
        article["title"] = "No Title"

    article["url"] = url
    return article
