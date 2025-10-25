import argparse
import os
from tqdm import tqdm
from output.writer import write_jsonl
from utils.logger import logger
from utils.db_utils import (
    fetch_pending_urls,
    update_url_status,
    insert_parsed_article,
    reset_old_error_urls,
    insert_urls_bulk,
)
import asyncio

from parser_core import process_url_async, process_url  

def load_urls_from_csv(csv_file):
    import csv
    urls = []
    try:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "url" not in reader.fieldnames:
                logger.error(f"CSV file missing 'url' column: {csv_file}")
                return []
            for row in reader:
                url = row.get("url")
                if url:
                    urls.append(url)
    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file}")
    except Exception as e:
        logger.exception(f"Error reading CSV file {csv_file}: {e}")
    return urls


def main():
    parser = argparse.ArgumentParser(description="Data Parser CLI Tool")
    parser.add_argument("--input", type=str, help="Path to CSV file containing URLs")
    parser.add_argument("--limit", type=int, help="Limit number of URLs to process", default=5)
    parser.add_argument("--reset-hours", type=int, help="Reset error URLs older than this many hours", default=24)
    parser.add_argument("--use-async", action="store_true", help="Use asynchronous fetching")
    args = parser.parse_args()

    reset_count = reset_old_error_urls(hours=args.reset_hours)
    if reset_count > 0:
        logger.info(f"Reset {reset_count} old 'error' URLs back to pending.")

    if args.input:
        urls = load_urls_from_csv(args.input)
        if urls:
            insert_urls_bulk(urls)
            logger.info(f"Inserted {len(urls)} URLs from {args.input} into database.")
        else:
            logger.warning("No valid URLs found in provided CSV file.")

    url_rows = fetch_pending_urls(limit=args.limit)
    if not url_rows:
        logger.info("No pending URLs found in database.")
        return

    logger.info(f"Processing {len(url_rows)} pending URLs...")

    if args.use_async:
        # call async processor from parser_core
        asyncio.run(process_url_async(url_rows))
    else:
        # synchronous processing
        os.makedirs("output_files", exist_ok=True)
        for row in tqdm(url_rows, desc="Parsing URLs"):
            url_id = row.get("id")
            url = row.get("url")
            if not url_id or not url:
                logger.warning(f"Skipping row with missing id or url: {row}")
                continue

            update_url_status(url_id, "processing")
            parsed = process_url(url)
            if parsed:
                filename = f"parsed_{url_id}.jsonl"
                file_path = os.path.join("output_files", filename)
                write_jsonl([parsed], file_path)
                insert_parsed_article(url_id, parsed["title"], file_path)
                update_url_status(url_id, "parsed")
            else:
                update_url_status(url_id, "error")

    logger.info("All URLs processed successfully.")


if __name__ == "__main__":
    main()
