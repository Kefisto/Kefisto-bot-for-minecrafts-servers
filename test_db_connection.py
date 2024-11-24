import pymysql
from pymysql import Error

DB_CONFIG = {
    'host': 'ip_address_here_here',
    'port': 3306,
    'user': 'user_here_here',
    'password': 'password_here_here',
    'database': 'bd_name_here',
}

try:
    conn = pymysql.connect(**DB_CONFIG)
    print("Successfully connected to the database")
    with conn.cursor() as cursor:
        cursor.execute("SELECT VERSION()")
        db_version = cursor.fetchone()
        print(f"Database version: {db_version[0]}")
except Error as err:
    print(f"Error: {err}")
finally:
    if 'conn' in locals() and conn.open:
        conn.close()
        print("Database connection closed")
