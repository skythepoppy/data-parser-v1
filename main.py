from parser_core import process_url
from output.writer import write_jsonl
from utils.logger import logger
from utils.db_utils import fetch_pending_urls, update_url_status, insert_parsed_article
from tqdm import tqdm
from utils.db_utils import reset_old_error_urls
import os

def main():
    
    reset_count = reset_old_error_urls(hours=24)
    if reset_count > 0:
        logger.info(f"Reset {reset_count} old 'error' URLs back to pending.")

    urls = fetch_pending_urls(limit=5)
    if not urls:
        logger.info("No pending URLs found in database.")
        return

    logger.info(f"Processing {len(urls)} pending URLs...")

    results = []

    for row in tqdm(urls, desc="Parsing URLs"):
        url_id = row["id"]
        url = row["url"]

        # Set status to 'processing'
        update_url_status(url_id, "processing")

        parsed = process_url(url)

        if parsed:
            results.append(parsed)

            # Write file for each parsed article
            filename = f"parsed_{url_id}.jsonl"
            file_path = os.path.join("output_files", filename)
            os.makedirs("output_files", exist_ok=True)

            write_jsonl([parsed], file_path)

            # Insert metadata into DB
            insert_parsed_article(url_id, parsed["title"], file_path)
            update_url_status(url_id, "parsed")
        else:
            update_url_status(url_id, "error")

    logger.info("All URLs processed.")

if __name__ == "__main__":
    main()
