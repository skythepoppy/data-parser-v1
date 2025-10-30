
from typing import Optional

def detect_format(url: str, content_type: str = "", data: bytes = None) -> str:
  
    
    #try furst content type header
    if content_type:
        content_type = content_type.lower()
        if "pdf" in content_type:
            return "pdf"
        if "json" in content_type:
            return "json"
        if "html" in content_type or "text" in content_type:
            return "html"
    
    # fallback to URL file extension
    if url.endswith(".pdf"):
        return "pdf"
    if url.endswith(".json"):
        return "json"
    if url.endswith(".html") or url.endswith(".htm"):
        return "html"
    
    #inspect the first bytes of data
    if data:
        if data.startswith(b"%PDF"):
            return "pdf"
        try:
            decoded = data.decode("utf-8", errors="ignore")
            if "<html" in decoded.lower():
                return "html"
        except Exception:
            pass
    
    
    return "html"
