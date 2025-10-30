import psycopg2
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
from dotenv import load_dotenv
import os

load_dotenv()

# Database connection settings
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def reset_stuck_urls():
    """Reset URLs stuck in 'processing' state or with old errors back to 'pending'"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Reset URLs stuck in processing
        cur.execute("""
            UPDATE urls 
            SET status = 'pending', 
                processed_at = NULL 
            WHERE status = 'processing'
            RETURNING id, url
        """)
        stuck_processing = cur.fetchall()
        
        # Reset old errors (>24h)
        cutoff = datetime.now() - timedelta(hours=24)
        cur.execute("""
            UPDATE urls 
            SET status = 'pending',
                processed_at = NULL
            WHERE status = 'error' 
            AND processed_at < %s
            RETURNING id, url
        """, (cutoff,))
        old_errors = cur.fetchall()
        
        conn.commit()
        
        if stuck_processing:
            logger.info("Reset %d URLs stuck in processing:", len(stuck_processing))
            for id, url in stuck_processing:
                logger.info(f"  - ID {id}: {url}")
                
        if old_errors:
            logger.info("Reset %d URLs with old errors:", len(old_errors))
            for id, url in old_errors:
                logger.info(f"  - ID {id}: {url}")
                
    except Exception as e:
        logger.error(f"Error resetting URLs: {e}")
        if conn:
            conn.rollback()
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    reset_stuck_urls()