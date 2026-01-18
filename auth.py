import hashlib
import psycopg2
from database import get_cursor

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def signup(username: str, password: str) -> bool:
    cursor = get_cursor()
    try:
        cursor.execute(
            """INSERT INTO users (username, password_hash) VALUES (%s, %s)""",(username, hash_password(password))
        )
        return True
    except psycopg2.errors.UniqueViolation:
        return False   # username already exists

    except Exception as e:
        print("Signup error:", e)
        return False

def login(username, password):
    cursor = get_cursor()
    cursor.execute(
        "SELECT id FROM users WHERE username=%s AND password_hash=%s",
        (username, hash_password(password))
    )
    return cursor.fetchone()

def user_exists(username: str) -> bool:
    cursor = get_cursor()
    cursor.execute(
        "SELECT id FROM users WHERE username=%s",
        (username,)
    )
    return cursor.fetchone() is not None
