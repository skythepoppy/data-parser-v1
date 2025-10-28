import markdown2
from utils.logger import logger
from bs4 import BeautifulSoup

def extract_markdown(md_text: str) -> dict:
    if not md_text:
        logger.warning("No markdown text provided to extract_markdown")
        return {"title": "No Title", "content": "No content available"}

    try:
        # html-markdown convert
        html = markdown2.markdown(md_text)

        # strimp html lines
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n").strip()

        #determine title as first non-empty line
        title = next((line.strip() for line in text.splitlines() if line.strip()), "No Title")

        if not text:
            logger.warning("Markdown conversion produced empty content")

        return {"title": title, "content": text or "No content available"}

    except Exception as e:
        logger.error(f"Failed to extract markdown content: {e}")
        return {"title": "No Title", "content": "No content available"}
