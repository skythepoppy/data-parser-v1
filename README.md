

## Overview  
This data-parser (v1) is a modular, asynchronous web scraping and content extraction pipeline.  
It fetches, extracts, cleans, and processes web articles into structured JSON data ready for analysis or storage.  

---

## Features
- **Asynchronous fetching** for concurrent scraping  
- **Modularity** (fetchers, extractors, cleaners, utils) with logging at each stage
- **JSON Output** : output parsed article data in JSON config  

---
## Dependencies
- `requests`
- `aiohttp`
- `tqdm`
- `beautifulsoup4`
- `argparse`
- `asyncio`

(Install all via `pip install -r requirements.txt`)
---

## Installation and Usage
1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/web-article-parser.git
   cd web-article-parser
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # (or venv\Scripts\activate via Windows)
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
4. **Usage (uploading URLs via .csv (can extract URLs from Postgres DB as well))**
   ```bash
   python main.py --input urls.csv --limit 10 --use-async
   ```

---

## Sample Output
Each parsed article is written into `output_files/` as a `.jsonl` file:

```json
{
  "url": "https://example.com/article1",
  "title": "Breaking News: Example Headline",
  "content": "This is the cleaned and extracted article text...",
  "author": "Jane Doe",
  "published_date": "2025-10-25"
}
```

## Logging
Logs are automatically written with context at each stage (fetching, extraction, cleaning, etc.).  
sample messages:

```
[INFO] process_url: fetched HTML for https://example.com/article1
[INFO] process_url: extracted article title successfully
[ERROR] process_url: extractor raised for https://badsite.com/article
```

---




