from selectolax.parser import HTMLParser
from utils.logger import logger
import re

def extract_article(html):
    if not html:
        logger.warning("No HTML provided to extract_article")
        return {"title": "No Title", "content": "No content available"}

    try:
        tree = HTMLParser(html)
    except Exception as e:
        logger.error(f"Failed to parse HTML: {e}")
        return {"title": "No Title", "content": "No content available"}

    # extract title 
    title = None
    title_selectors = ["h1", "h2", "title", "meta[property='og:title']", "meta[name='title']"]
    for selector in title_selectors:
        element = tree.css_first(selector)
        if element:
            if selector.startswith("meta"):
                title_text = element.attributes.get("content", "").strip()
            else:
                title_text = element.text().strip()
            if title_text:
                title = title_text
                break

    if not title:
        #fallback here 
        for div in tree.css("div, section"):
            text = div.text().strip()
            if text and len(text) < 200:  
                title = text
                break

    title = title or "No Title"
    if title == "No Title":
        logger.warning("No title found in HTML")

    # extract main content 
    candidate_tags = ["article", "section", "div", "main"]
    candidates = []

    for tag in candidate_tags:
        for element in tree.css(tag):
            text = element.text().strip()
            if text:
                ## computation for text density
                tag_count = len(element.css("*")) or 1
                density = len(text) / tag_count
                candidates.append((density, text))

    # sort by descnending density
    candidates.sort(reverse=True, key=lambda x: x[0])

    content = None
    for _, text in candidates:
        # filter out short texts or boiler plates
        if len(text) > 100 and not re.match(r"^\s*(advertisement|cookie|subscribe|privacy|terms)", text, re.I):
            content = text
            break

    # fallback to all <p> tags if null
    if not content:
        paragraphs = [p.text().strip() for p in tree.css("p") if p.text().strip() and len(p.text().strip()) > 30]
        if paragraphs:
            content = "\n".join(paragraphs)
        else:
            logger.warning("No meaningful paragraphs found in HTML")
            content = "No content available"

    return {"title": title, "content": content}
