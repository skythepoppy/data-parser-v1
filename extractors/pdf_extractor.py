
import pdfplumber
from utils.logger import logger

def extract_pdf(file_path: str) -> dict:
    content = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                content += page.extract_text() + "\n"
    except Exception as e:
        logger.error(f"Failed to extract PDF {file_path}: {e}")
        return {"title": "No Title", "content": "No content available"}

    title = file_path.split("/")[-1]
    return {"title": title, "content": content.strip() or "No content available"}
