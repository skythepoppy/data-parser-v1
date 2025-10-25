import requests
from utils.logger import logger
from time import sleep

def fetch_html(url, retries=3, backoff=2, headers=None, timeout=10):
    default_headers = {"User-Agent": "Mozilla/5.0 (compatible; DataParser/1.0)"}
    if headers:
        default_headers.update(headers)

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=timeout, headers=default_headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt} failed to fetch {url}: {e}")
            if attempt < retries:
                sleep(backoff * attempt)
            else:
                logger.error(f"Failed to fetch {url} after {retries} attempts.")
                return None
