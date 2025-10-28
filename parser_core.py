import os
import asyncio
from typing import Optional, Dict, Any
import aiohttp
from cleaners.text_cleaner import clean_text
from utils.logger import logger
from utils.db_utils import update_url_status, insert_parsed_article
from output.writer import write_jsonl
from utils.format_detector import detect_format
from extractors.universal_extractor import extract_content
from enrichers.semantic_enricher import enrich_text


# wrapper for cpiu heavy operations
async def enrich_text_async(article: Dict[str, Any]) -> Dict[str, Any]:
    
    try:
        return await asyncio.to_thread(enrich_text, article)
    except Exception as e:
        logger.error(f"Async semantic enrichment failed: {e}")
        return article


async def fetch_content_async(url: str, session: aiohttp.ClientSession, retries: int = 3, backoff: int = 2) -> Optional[Dict[str, Any]]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DataParser/1.0)"}
    for attempt in range(1, retries + 1):
        try:
            async with session.get(url, timeout=10, headers=headers) as response:
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


# shared extract and enrichment for a single url
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

    # semantic enrichment
    article = await enrich_text_async(article)
    return article


async def process_url_async(url: str, session: aiohttp.ClientSession, lowercase_content: bool = False) -> Optional[Dict[str, Any]]:
    if not url or not isinstance(url, str):
        logger.error("Invalid URL input: %r", url)
        return None

    fetched = await fetch_content_async(url, session)
    if not fetched:
        logger.warning("No content returned for %s", url)
        return None

    format_type = detect_format(url, fetched["content_type"], data=fetched["data"])
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
