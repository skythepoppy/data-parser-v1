import argparse
import csv
import os
from tqdm import tqdm
from parser_core import process_url
from output.writer import write_jsonl
from utils.logger import logger
from utils.db_utils import (
    fetch_pending_urls,
    update_url_status,
    insert_parsed_article,
    reset_old_error_urls,
    insert_urls_bulk,  
)

def load_urls_from_csv(file_path):
    """Reads a CSV file and returns a list of URLs."""
    urls = []
    with open(file_path, "r", newline="", encoding="utf-8") as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row and row[0].startswith("http"):
                urls.append(row[0].strip())
    return urls


def main():
    parser = argparse.ArgumentParser(description="Data Parser CLI Tool")
    parser.add_argument("--input", type=str, help="Path to CSV file containing URLs")
    parser.add_argument("--limit", type=int, help="Limit number of URLs to process", default=5)
    parser.add_argument("--reset-hours", type=int, help="Reset error URLs older than this many hours", default=24)
    args = parser.parse_args()

    # reset old urls
    reset_count = reset_old_error_urls(hours=args.reset_hours)
    if reset_count > 0:
        logger.info(f"Reset {reset_count} old 'error' URLs back to pending.")

    # option to import urls via csv
    if args.input:
        urls = load_urls_from_csv(args.input)
        if urls:
            insert_urls_bulk(urls)
            logger.info(f"Inserted {len(urls)} URLs from {args.input} into database.")
        else:
            logger.warning("No valid URLs found in provided CSV file.")

    # \fetch urls for processing
    urls = fetch_pending_urls(limit=args.limit)
    if not urls:
        logger.info("No pending URLs found in database.")
        return

    logger.info(f"Processing {len(urls)} pending URLs...")
    results = []

    for row in tqdm(urls, desc="Parsing URLs"):
        url_id = row["id"]
        url = row["url"]

        update_url_status(url_id, "processing")
        parsed = process_url(url)

        if parsed:
            results.append(parsed)
            os.makedirs("output_files", exist_ok=True)
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
