import json
from utils.logger import logger

def write_jsonl(data, filename):
    if not data:
        logger.warning("No data to write to JSONL")
        return

    with open(filename, "w", encoding="utf-8") as f:
        for entry in data:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    logger.info(f"Wrote {len(data)} entries to {filename}")
