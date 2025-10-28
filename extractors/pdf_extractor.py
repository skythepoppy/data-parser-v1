import pdfplumber
from utils.logger import logger

def extract_pdf(file_path: str) -> dict:
    if not file_path:
        logger.warning("No file path provided to extract_pdf")
        return {"title": "No Title", "content": "No content available"}

    content_lines = []

    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    content_lines.extend(page_text.splitlines())
    except Exception as e:
        logger.error(f"Failed to extract PDF {file_path}: {e}")
        return {"title": "No Title", "content": "No content available"}

    if not content_lines:
        logger.warning(f"No text found in PDF: {file_path}")
        return {"title": "No Title", "content": "No content available"}

    # use first nonempty line as title (if needed )
    title = next((line.strip() for line in content_lines if line.strip()), file_path.split("/")[-1])

    content = "\n".join(content_lines).strip()
    return {"title": title, "content": content or "No content available"}
