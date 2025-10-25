import requests
from utils.logger import logger
from time import sleep

def fetch_html(url, retries=3, backoff=2):

    headers = {
    }
    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=10, headers=headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.warning(f"Attempt {attempt} failed to fetch {url}: {e}")
            if attempt < retries:
                sleep(backoff * attempt)
            else:
                logger.error(f"Failed to fetch {url} after {retries} attempts.")
                return None
