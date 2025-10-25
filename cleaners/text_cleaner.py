import re
from utils.logger import logger

def clean_text(text, lowercase=False):

    if not text:
        logger.warning("clean_text: received empty or None text")
        return ""

    # remove URLs
    text = re.sub(r"http\S+", "", text)
    
    # whitespace normalization
    text = re.sub(r"\s+", " ", text)
    
    # remove unwanted char, keep punct and unicode char
    text = re.sub(r"[^\w\s.,!?;:'\"()-]", "", text, flags=re.UNICODE)
    
    cleaned = text.strip()
    return cleaned.lower() if lowercase else cleaned
