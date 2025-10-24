""" will handle connecting to postgres DB, fetch URLs, uupddate URL status
store metadata"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime, timezone


load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

def get_connection():
    connection = psycopg2.connect(
        dbname=DB_NAME, 
        user=DB_USER, 
        password=DB_PASSWORD, 
        host=DB_HOST, 
        port=DB_PORT
    )
    return connection

def fetch_pending_urls(limit=10): 
    connection = get_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM urls WHERE status='processing' ORDER BY created_at LIMIT %s", (limit,))
    urls = cursor.fetchall()
    cursor.close()
    connection.close()
    return urls

def update_url_status(url_id, status):
    connection = get_connection()
    cursor = connection.cursor()
    if status == "done":
        cursor.execute(
            "UPDATE urls SET status=%s, processed_at=%s WHERE id=%s",
            (status, datetime.now(timezone.utc), url_id),
        )
    else:
        cursor.execute(
            "UPDATE urls SET status=%s WHERE id=%s",
            (status, url_id),
        )
    connection.commit()
    cursor.close()
    connection.close()

def insert_parsed_article(url_id, title, file_path): 
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO parsed_articles (url_id, title, file_path) VALUES (%s, %s, %s)",
        (url_id, title, file_path))
    connection.commit()
    cursor.close()
    connection.close()