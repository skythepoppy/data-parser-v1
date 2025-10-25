from selectolax.parser import HTMLParser
from utils.logger import logger

def extract_article(html):
    if not html:
        # missing/malformed html
        logger.warning("No HTML provided to extract_article")
        return {"title": "No Title", "content": "No content available"}

    try:
        tree = HTMLParser(html)
    except Exception as e:
        logger.error(f"Failed to parse HTML: {e}")
        return {"title": "No Title", "content": "No content available"}

    # for title
    h1 = tree.css_first("h1")
    title_tag = tree.css_first("title")
    title = h1.text().strip() if h1 else (title_tag.text().strip() if title_tag else "No Title")
    if title == "No Title":
        logger.warning("No title found in HTML")

    # for paragrpahs
    paragraphs = [p.text().strip() for p in tree.css("p") if p.text().strip()]
    if not paragraphs:
        logger.warning("No paragraphs found in HTML")
    content = "\n".join(paragraphs) or "No content available"

    return {"title": title, "content": content}
