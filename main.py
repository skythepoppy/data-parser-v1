from parser_core import process_url
from output.writer import write_jsonl
from utils.logger import logger
from tqdm import tqdm

def main():
    urls = [
        "https://example.com",
        "https://www.python.org/about/"
    ]

    results = []
    logger.info(f"Parsing {len(urls)} URLs...")
    
    for url in tqdm(urls, desc="Parsing URLs"):
        parsed = process_url(url)
        if parsed:
            results.append(parsed)
        else:
            logger.warning(f"Skipping URL due to errors: {url}")

    output_file = "parsed_output.jsonl"
    write_jsonl(results, output_file)
    logger.info(f"Parsing complete. Saved {len(results)} articles to {output_file}")

if __name__ == "__main__":
    main()
