import os
import asyncio
from typing import Optional, Dict, Any
import aiohttp
import ssl
import certifi
from cleaners.text_cleaner import clean_text
from utils.logger import logger
from utils.db_utils import update_url_status, insert_parsed_article
from output.writer import write_jsonl
from utils.format_detector import detect_format
from extractors.universal_extractor import extract_content
from enrichers.semantic_enricher import enrich_text
from utils.prompttracker_client import send_to_prompttracker

# --- import our new model loader ---
from utils.parser_models import load_models

# Load models once at startup
models = load_models()

# --- helpers for normalization ---
def normalize_keywords(keywords):
    if not keywords:
        return []
    normalized = []
    for kw in keywords:
        if isinstance(kw, list) and len(kw) == 2:
            normalized.append({"keyword": kw[0], "score": kw[1]})
        else:
            normalized.append({"keyword": str(kw), "score": None})
    return normalized

def normalize_parsed_article(parsed: Dict[str, Any]) -> Dict[str, Any]:
    parsed["keywords"] = normalize_keywords(parsed.get("keywords"))
    # summary should be string or None
    parsed["summary"] = str(parsed.get("summary")) if parsed.get("summary") is not None else None
    # sentiment should be dict or None
    parsed["sentiment"] = parsed.get("sentiment") if isinstance(parsed.get("sentiment"), dict) else None
    # entities should be list/dict or None
    parsed["entities"] = parsed.get("entities") if parsed.get("entities") else None
    return parsed

# --- wrappers for CPU-heavy operations ---
async def enrich_text_async(article: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return await asyncio.to_thread(enrich_text, article)
    except Exception as e:
        logger.error(f"Async semantic enrichment failed: {e}")
        return article

async def summarize_text_async(text: str) -> Optional[str]:
    if not text or not models.get("summarizer"):
        return None
    try:
        return await asyncio.to_thread(
            lambda: models["summarizer"](text, max_length=150, min_length=30, do_sample=False)[0]["summary_text"]
        )
    except Exception as e:
        logger.error(f"Async summarization failed: {e}")
        return None

async def extract_keywords_async(text: str) -> Optional[list]:
    if not text or not models.get("keybert"):
        return None
    try:
        return await asyncio.to_thread(
            lambda: models["keybert"].extract_keywords(
                text, keyphrase_ngram_range=(1, 2), stop_words="english"
            )
        )
    except Exception as e:
        logger.error(f"Async keyword extraction failed: {e}")
        return None

async def analyze_sentiment_async(text: str) -> Optional[dict]:
    if not text or not models.get("sentiment"):
        return None
    try:
        return await asyncio.to_thread(
            lambda: models["sentiment"](text)[0]  # dict with label + score
        )
    except Exception as e:
        logger.error(f"Async sentiment analysis failed: {e}")
        return None

# --- async content fetcher ---
async def fetch_content_async(url: str, session: aiohttp.ClientSession, retries: int = 3, backoff: int = 2) -> Optional[Dict[str, Any]]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DataParser/1.0)"}
    ssl_context = ssl.create_default_context(cafile=certifi.where())

    for attempt in range(1, retries + 1):
        try:
            async with session.get(url, timeout=10, headers=headers, ssl=ssl_context) as response:
                response.raise_for_status()
                return {
                    "data": await response.read(),
                    "content_type": response.headers.get("Content-Type", "")
                }
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"Attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                await asyncio.sleep(backoff * attempt)
            else:
                logger.error(f"Failed to fetch {url} after {retries} attempts")
                return None

# --- extract and enrich ---
async def extract_and_enrich(content_data: bytes, url: str, format_type: str, lowercase_content: bool) -> Optional[Dict[str, Any]]:
    try:
        if format_type == "pdf":
            tmp_file = f"temp_{os.getpid()}.pdf"
            with open(tmp_file, "wb") as f:
                f.write(content_data)
            article = extract_content(tmp_file, source_type="pdf")
            os.remove(tmp_file)
        else:
            text_content = content_data.decode("utf-8", errors="ignore")
            article = extract_content(text_content, source_type=format_type)
    except Exception as e:
        logger.exception(f"Extractor raised exception for {url}: {e}")
        return None

    if not isinstance(article, dict):
        logger.error("Extractor returned non-dict for %s: %r", url, article)
        return None

    content_text = str(article.get("content") or "").strip()
    article["content"] = clean_text(content_text, lowercase=lowercase_content) if content_text else "No content available"
    article["title"] = article.get("title") or "No Title"
    article["url"] = url

    # --- semantic enrichment ---
    article = await enrich_text_async(article)

    # --- generate summary, keywords, sentiment ---
    article["summary"] = await summarize_text_async(content_text)
    article["keywords"] = await extract_keywords_async(content_text)
    article["sentiment"] = await analyze_sentiment_async(content_text)

    # --- normalize for Postgres ---
    article = normalize_parsed_article(article)

    return article

# --- async URL processing ---
async def process_url_async(url: str, session: aiohttp.ClientSession, lowercase_content: bool = False) -> Optional[Dict[str, Any]]:
    if not url or not isinstance(url, str):
        logger.error("Invalid URL input: %r", url)
        return None

    fetched = await fetch_content_async(url, session)
    if not fetched:
        logger.warning("No content returned for %s", url)
        return None

    format_type = detect_format(url, fetched["content_type"], data=fetched.get("data"))
    return await extract_and_enrich(fetched["data"], url, format_type, lowercase_content)

async def process_urls_async(url_rows, lowercase_content: bool = False):
    results = []
    os.makedirs("output_files", exist_ok=True)

    async with aiohttp.ClientSession() as session:

        async def handle_row(row):
            url_id = row.get("id")
            url = row.get("url")
            if url_id is None or not url:
                logger.warning(f"Skipping row with missing 'id' or 'url': {row}")
                return

            update_url_status(url_id, "processing")
            parsed = await process_url_async(url, session, lowercase_content)
            if parsed:
                results.append(parsed)
                filename = f"parsed_{url_id}.jsonl"
                file_path = os.path.join("output_files", filename)
                write_jsonl([parsed], file_path)

                insert_parsed_article(
                    url_id,
                    parsed["title"],
                    file_path,
                    keywords=parsed.get("keywords"),
                    summary=parsed.get("summary"),
                    sentiment=parsed.get("sentiment"),
                    entities=parsed.get("entities")
                )

                try:
                    send_to_prompttracker(parsed)
                except Exception as e:
                    logger.error(f"Failed to push parsed article to PromptTracker: {e}")

                update_url_status(url_id, "parsed")
            else:
                update_url_status(url_id, "error")

        await asyncio.gather(*(handle_row(row) for row in url_rows))

    return results

def process_url(url: str, lowercase_content: bool = False) -> Optional[Dict[str, Any]]:
    async def _runner():
        async with aiohttp.ClientSession() as session:
            return await process_url_async(url, session, lowercase_content)
    return asyncio.run(_runner())
