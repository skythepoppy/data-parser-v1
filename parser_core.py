import os
import asyncio
from typing import Optional, Dict, Any
import aiohttp
from extractors.html_extractor import extract_article
from cleaners.text_cleaner import clean_text
from utils.logger import logger
from utils.db_utils import update_url_status, insert_parsed_article
from output.writer import write_jsonl


async def fetch_html_async(url: str, session: aiohttp.ClientSession, retries: int = 3, backoff: int = 2) -> Optional[str]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DataParser/1.0)"}

    for attempt in range(1, retries + 1):
        try:
            async with session.get(url, timeout=10, headers=headers) as response:
                response.raise_for_status()
                return await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.warning(f"Attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                await asyncio.sleep(backoff * attempt)
            else:
                logger.error(f"Failed to fetch {url} after {retries} attempts")
                return None


async def process_url_async(url: str, session: aiohttp.ClientSession, lowercase_content: bool = False) -> Optional[Dict[str, Any]]:
    if not url or not isinstance(url, str):
        logger.error("Invalid URL input: %r", url)
        return None

    html = await fetch_html_async(url, session)
    if not html:
        logger.warning("No HTML returned for %s", url)
        return None

    try:
        article = extract_article(html)
    except Exception:
        logger.exception("Extractor raised exception for %s", url)
        return None

    if not isinstance(article, dict):
        logger.error("Extractor returned non-dict for %s: %r", url, article)
        return None

    content_text = str(article.get("content") or "").strip()
    if not content_text or content_text.lower() == "none":
        logger.warning("Empty content for %s", url)
        article["content"] = "No content available"
    else:
        article["content"] = clean_text(content_text, lowercase=lowercase_content)

    if not article.get("title"):
        logger.warning("No title found for %s", url)
        article["title"] = "No Title"

    article["url"] = url
    return article


async def process_urls_async(url_rows, lowercase_content: bool = False):
    """
    Processes multiple URL rows concurrently using a single aiohttp session.
    url_rows: list of dicts containing at least {"id": int, "url": str}
    """
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
                insert_parsed_article(url_id, parsed["title"], file_path)
                update_url_status(url_id, "parsed")
            else:
                update_url_status(url_id, "error")

        tasks = [handle_row(row) for row in url_rows]
        await asyncio.gather(*tasks)

    return results


def process_url(url: str, lowercase_content: bool = False) -> Optional[Dict[str, Any]]:
    """
    Synchronous wrapper to process a single URL using the async workflow.
    """
    async def _runner():
        async with aiohttp.ClientSession() as session:
            return await process_url_async(url, session, lowercase_content)

    return asyncio.run(_runner())
