
import markdown2
from utils.logger import logger

def extract_markdown(md_text: str) -> dict:
    if not md_text:
        return {"title": "No Title", "content": "No content available"}

    # Convert markdown to HTML then strip tags if needed
    html = markdown2.markdown(md_text)
    text = "".join(html.splitlines())
    title = text.split("\n")[0] if text else "No Title"
    return {"title": title, "content": text or "No content available"}
