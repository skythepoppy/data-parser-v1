from selectolax.parser import HTMLParser
from utils.logger import logger

def extract_article(html):
    tree = HTMLParser(html)

   
    h1 = tree.css_first("h1")
    title = h1.text().strip() if h1 else "No Title"


    paragraphs = [p.text().strip() for p in tree.css("p") if p.text().strip()]
    if not paragraphs:
        logger.warning("No paragraphs found in HTML")
    content = "\n".join(paragraphs)


    return {
        "title": title,
        "content": content or "No content available"
    }
