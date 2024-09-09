import mysql.connector

def get_db_connection():
    """Establish and return a MySQL database connection."""
    return mysql.connector.connect(
        host='localhost',
        user='pinpoint',
        password='pinpoint',
        database='mukhmondol'
    )
