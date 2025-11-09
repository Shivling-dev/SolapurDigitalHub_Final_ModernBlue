import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    import mysql.connector
    from mysql.connector import Error
except ImportError:
    mysql = None
    Error = Exception

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', '')
DB_NAME = os.getenv('DB_NAME', 'solapur_digital_hub')


def get_connection():
    """Try connecting to MySQL, else run in safe (no-DB) mode."""
    if not mysql:
        print("⚠️ mysql.connector not available — running in No-DB mode")
        return None

    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASS,
            database=DB_NAME
        )
        if conn.is_connected():
            print(f"✅ Connected to MySQL database '{DB_NAME}' as user '{DB_USER}'")
            return conn
        else:
            print("❌ Connection object created but not connected")
            return None
    except Error as e:
        print('⚠️ DB connection skipped (No MySQL found):', e)
        return None
