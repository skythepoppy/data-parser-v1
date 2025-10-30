import psycopg2

conn = None
try:
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    conn = psycopg2.connect(
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    cur = conn.cursor()
    cur.execute("SELECT id, url_id, title, file_path, fetched_at, keywords IS NOT NULL as has_keywords FROM parsed_articles ORDER BY fetched_at DESC LIMIT 10")
    rows = cur.fetchall()
    print('Recent parsed_articles:')
    for r in rows:
        print(r)
    cur.close()
except Exception as e:
    print('Error querying parsed_articles:', e)
finally:
    if conn:
        conn.close()