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
from semantic_enricher import enrich_text

async def fetch_content_async(url: str, session: aiohttp.ClientSession, retries: int = 3, backoff: int = 2) -> Optional[Dict[str, Any]]:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; DataParser/1.0)"}

    for attempt in range(1, retries + 1):
        try:
            async with session.get(url, timeout=10, headers=headers) as response:
                response.raise_for_status()
                content_type = response.headers.get("Content-Type", "")
                data = await response.read()  # binary-safe for PDFs
                return {"data": data, "content_type": content_type}
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

    fetched = await fetch_content_async(url, session)
    if not fetched:
        logger.warning("No content returned for %s", url)
        return None

    content_data = fetched["data"]
    content_type = fetched["content_type"]

    # detection using content bytes
    format_type = detect_format(url, content_type, data=content_data)

    try:
        if format_type == "pdf":
            # save PDF temporarily for extraction
            tmp_file = f"temp_{os.getpid()}.pdf"
            with open(tmp_file, "wb") as f:
                f.write(content_data)
            article = extract_content(tmp_file, source_type="pdf")
            os.remove(tmp_file)
        else:
            # decode bytes for HTML/Markdown/plain text
            text_content = content_data.decode("utf-8", errors="ignore")
            article = extract_content(text_content, source_type=format_type)
    except Exception as e:
        logger.exception(f"Extractor raised exception for {url}: {e}")
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

    # implementation of semantic enrichment 
    try:
        article = enrich_text(article)
    except Exception as e:
        logger.error(f"Semantic enrichment failed for {url}: {e}")
    return article



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
                insert_parsed_article(url_id, parsed["title"], file_path)
                update_url_status(url_id, "parsed")
            else:
                update_url_status(url_id, "error")

        tasks = [handle_row(row) for row in url_rows]
        await asyncio.gather(*tasks)

    return results


def process_url(url: str, lowercase_content: bool = False) -> Optional[Dict[str, Any]]:
   
    async def _runner():
        async with aiohttp.ClientSession() as session:
            article = await process_url_async(url, session, lowercase_content)
            #use enrichment from async funct
            return article

    return asyncio.run(_runner())

