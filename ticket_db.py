import mysql.connector
from mysql.connector import Error, errorcode
from functools import wraps
import traceback

# Настройки подключения к базе данных
DB_CONFIG = {
    'host': 'ip', #Айпи адрес без порта!
    'user': 'user',
    'password': 'password',
    'database': 'bd_name',
    'raise_on_warnings': True,
    'use_pure': True,
    'autocommit': True,
    'pool_size': 5
}


def db_connection(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            return func(conn, *args, **kwargs)
        except mysql.connector.Error as err:
            print(f"MySQL Error: {err}")
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Error: Invalid username or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Error: Database does not exist")
            else:
                print(f"Error: {err}")
            print(f"Full traceback: {traceback.format_exc()}")
        except Exception as e:
            print(f"Unexpected error: {e}")
            print(f"Full traceback: {traceback.format_exc()}")
        finally:
            if conn and conn.is_connected():
                conn.close()
    return wrapper

@db_connection
def init_db(conn):
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            user_id BIGINT PRIMARY KEY,
            created_at DATETIME
        )
    ''')
    conn.commit()

@db_connection
def user_has_ticket(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tickets WHERE user_id = %s", (user_id,))
    return cursor.fetchone() is not None

@db_connection
def add_ticket(conn, user_id, created_at):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tickets (user_id, created_at) VALUES (%s, %s)", (user_id, created_at))
    conn.commit()

@db_connection
def remove_ticket(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tickets WHERE user_id = %s", (user_id,))
    conn.commit()
