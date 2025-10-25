from selectolax.parser import HTMLParser
from utils.logger import logger

def extract_article(html):
  
    if not html:
        logger.warning("No HTML provided to extract_article")
        return {"title": "No Title", "content": "No content available"}

    try:
        tree = HTMLParser(html)
    except Exception as e:
        logger.error(f"Failed to parse HTML: {e}")
        return {"title": "No Title", "content": "No content available"}

    # title
    title = None
    for tag in ["h1", "h2", "title"]:
        element = tree.css_first(tag)
        if element and element.text().strip():
            title = element.text().strip()
            break
    title = title or "No Title"
    if title == "No Title":
        logger.warning("No title found in HTML")

    # paragraphs
    paragraphs = [p.text().strip() for p in tree.css("p") if p.text().strip()]
    if not paragraphs:
        logger.warning("No paragraphs found in HTML")
    content = "\n".join(paragraphs) or "No content available"

    return {"title": title, "content": content}
