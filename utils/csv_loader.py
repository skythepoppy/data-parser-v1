import csv
import sys
from datetime import datetime
from utils.db_utils import get_connection, logger

def load_urls_from_csv(csv_file_path: str):
    connection = get_connection()
    cursor = connection.cursor()

    inserted_count = 0
    try:
        with open(csv_file_path, "r", encoding="utf-8") as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                url = row.get("url")
                if not url:
                    continue
                # Insert URL, ignore duplicates
                cursor.execute(
                    """
                    INSERT INTO urls (url, status, created_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (url) DO NOTHING
                    """,
                    (url, "pending", datetime.utcnow())
                )
                inserted_count += 1

        connection.commit()
        logger.info(f"Inserted {inserted_count} URLs from {csv_file_path}")

    except FileNotFoundError:
        logger.error(f"CSV file not found: {csv_file_path}")
    except Exception as e:
        logger.exception(f"Error inserting URLs from CSV: {e}")
    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.error("Usage: python csv_loader.py <path_to_csv>")
    else:
        csv_file = sys.argv[1]
        load_urls_from_csv(csv_file)
