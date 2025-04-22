import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "database": "jogging",
    "user": "root",  # Change as needed
    "password": "",  # Change as needed
}


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    connection = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        yield connection
    except Error as e:
        print(f"Database error: {e}")
        raise
    finally:
        if connection and connection.is_connected():
            connection.close()


@contextmanager
def get_db_cursor(commit=False, connection=None):
    """Context manager for database cursor.
    
    Args:
        commit (bool): Whether to commit changes at the end
        connection (Connection): An existing connection to use, or None to create a new one
    """
    close_connection = False
    if connection is None:
        connection = mysql.connector.connect(**DB_CONFIG)
        close_connection = True
    
    cursor = connection.cursor(dictionary=True)
    try:
        yield cursor
        if commit:
            connection.commit()
    except Error as e:
        connection.rollback()
        print(f"Database error: {e}")
        raise
    finally:
        cursor.close()
        if close_connection and connection and connection.is_connected():
            connection.close()
