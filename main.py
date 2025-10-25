import argparse
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
    args = parser.parse_args()

    # resetting olr urls
    reset_count = reset_old_error_urls(hours=args.reset_hours)
    if reset_count > 0:
        logger.info(f"Reset {reset_count} old 'error' URLs back to pending.")

    # load urls from csv
    if args.input:
        urls = load_urls_from_csv(args.input)
        if urls:
            insert_urls_bulk(urls)
            logger.info(f"Inserted {len(urls)} URLs from {args.input} into database.")
        else:
            logger.warning("No valid URLs found in provided CSV file.")

    # fetch processing urls
    urls = fetch_pending_urls(limit=args.limit)
    if not urls:
        logger.info("No pending URLs found in database.")
        return

    logger.info(f"Processing {len(urls)} pending URLs...")

    results = []
    os.makedirs("output_files", exist_ok=True)  

    for row in tqdm(urls, desc="Parsing URLs"):
        url_id = row["id"]
        url = row["url"]

        update_url_status(url_id, "processing")
        parsed = process_url(url)

        if parsed:
            results.append(parsed)
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
