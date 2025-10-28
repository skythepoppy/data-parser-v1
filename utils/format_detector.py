
import mimetypes
import os
from urllib.parse import urlparse

def detect_format(url: str, content_type: str = None) -> str:
   
    if content_type:
        if "text/html" in content_type:
            return "html"
        if "application/pdf" in content_type:
            return "pdf"
        if "application/json" in content_type:
            return "json"
        if "text/markdown" in content_type:
            return "markdown"


    # end of file path check
    path = urlparse(url).path
    ext = os.path.splitext(path)[1].lower()
    if ext in [".html", ".htm"]:
        return "html"
    if ext == ".pdf":
        return "pdf"
    if ext == ".md":
        return "markdown"
    if ext == ".json":
        return "json"

    return "unknown"
