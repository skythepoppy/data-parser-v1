from parser_core import process_url
from output.writer import write_jsonl
from tqdm import tqdm

def main():
    urls = [
        "https://example.com",  
        "https://www.bbc.com/news/world",
    ]

    results = []
    for url in tqdm(urls, desc="Parsing URLs"):
        parsed = process_url(url)
        if parsed:
            results.append(parsed)

    write_jsonl(results, "parsed_output.jsonl")
    print("✅ Parsing complete. Saved to parsed_output.jsonl")

if __name__ == "__main__":
    main()
