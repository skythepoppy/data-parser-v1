import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from utils.logger import logger
from datetime import datetime

# URL for the PromptTracker API endpoint (override with environment variable if needed)
PROMPT_TRACKER_URL = os.getenv("PROMPT_TRACKER_URL", "http://localhost:5295/api/prompt/import")

# Configure retry strategy
retry_strategy = Retry(
    total=3,  # number of retries
    backoff_factor=1,  # wait 1, 2, 4 seconds between retries
    status_forcelist=[500, 502, 503, 504]  # HTTP status codes to retry on
)

# Create session with retry strategy
session = requests.Session()
adapter = HTTPAdapter(max_retries=retry_strategy)
session.mount("http://", adapter)
session.mount("https://", adapter)


def classify_category(text: str) -> str:
    lower_text = text.lower()
    if any(word in lower_text for word in ["code", "program", "bug", "algorithm", "api", "c#", "python", "java"]):
        return "Coding"
    elif any(word in lower_text for word in ["write", "essay", "story", "paragraph", "poem"]):
        return "Writing"
    elif any(word in lower_text for word in ["math", "equation", "calculate", "solve", "formula"]):
        return "Math"
    elif any(word in lower_text for word in ["data", "analyze", "statistics", "ai", "ml", "training"]):
        return "AI/Analytics"
    else:
        return "General"


def truncate_text(text: str, max_length: int = 500) -> str:
    """Truncate text to max_length while preserving word boundaries"""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length].rsplit(' ', 1)[0] + '...'

def send_to_prompttracker(article: dict):
    try:
        title = article.get("title", "Untitled Article")
        summary = article.get("summary") or ""

        # normalize keywords: may be list[str] or list[dict]{keyword,score}
        raw_keywords = article.get("keywords") or []
        keywords_list = []
        if raw_keywords:
            if isinstance(raw_keywords[0], dict) and "keyword" in raw_keywords[0]:
                keywords_list = [str(k.get("keyword", "")) for k in raw_keywords]
            else:
                keywords_list = [str(k) for k in raw_keywords]

        # normalize entities: may be None, list[str], or list[dict]{text}
        raw_entities = article.get("entities") or []
        entities_list = []
        for e in raw_entities:
            if isinstance(e, dict) and "text" in e:
                entities_list.append(str(e["text"]))
            else:
                entities_list.append(str(e))

        keywords_str = ", ".join(keywords_list)
        entities_str = ", ".join(entities_list)

        # Build payload matching PromptTracker's ParserImportDto
        payload = {
            "Summary": truncate_text(summary or "No summary available", 500),
            "Keywords": truncate_text(keywords_str, 200),
            "Entities": truncate_text(entities_str, 200),
            "FetchedAt": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%fZ")  # Format compatible with ASP.NET Core
        }

        logger.debug("PromptTracker import payload: %s", payload)
        response = session.post(PROMPT_TRACKER_URL, json=payload, timeout=10)  # Use session with retry logic

        if not (200 <= response.status_code < 300):
            logger.error(
                "PromptTracker returned %s for article '%s': %s",
                response.status_code,
                title,
                response.text,
            )

        response.raise_for_status()

        logger.info(f"Imported article '{title}' to PromptTracker (status {response.status_code})")

    except Exception as e:
        # ensure title variable exists in exception path
        t = locals().get("title", "<unknown>")
        logger.error(f"Failed to send article '{t}' to PromptTracker: {e}")

