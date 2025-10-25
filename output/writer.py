import json
import os
from utils.logger import logger

def write_jsonl(data, filename, append=False):
    if not data:
        logger.warning("No data to write to JSONL")
        return 0

    mode = "a" if append else "w"
    os.makedirs(os.path.dirname(filename), exist_ok=True)

    try:
        with open(filename, mode, encoding="utf-8") as f:
            for entry in data:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        logger.info(f"Wrote {len(data)} entries to {filename}")
        return len(data)
    except Exception as e:
        logger.exception(f"Failed to write JSONL to {filename}: {e}")
        return 0
