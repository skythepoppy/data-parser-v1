from extractors.html_extractor import extract_article
from extractors.pdf_extractor import extract_pdf
from extractors.markdown_extractor import extract_markdown
from utils.logger import logger
import os

def extract_content(source: str, source_type: str = None) -> dict:
    try:
        if not source:
            logger.warning("extract_content: received empty source")
            return {"title": "No Title", "content": "No content available"}

        # infer type based on extension
        if source_type is None:
            if os.path.isfile(source):
                ext = os.path.splitext(source)[1].lower()
                if ext == ".pdf":
                    source_type = "pdf"
                elif ext == ".md":
                    source_type = "markdown"
                else:
                    source_type = "html"
            else:
                # if not file, then default to html type 
                source_type = "html"

        # assign to respective extractors
        if source_type == "html":
            return extract_article(source)
        elif source_type == "pdf":
            return extract_pdf(source)
        elif source_type == "markdown":
            return extract_markdown(source)
        else:
            logger.warning(f"Unknown source type '{source_type}', defaulting to HTML")
            return extract_article(source)

    except Exception as e:
        logger.error(f"Universal extractor failed: {e}")
        return {"title": "No Title", "content": "No content available"}
