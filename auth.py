import hashlib
import psycopg2
from database import get_connection

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# ---------------- SIGNUP ----------------

def signup(username: str, password: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (username, hash_password(password))
        )
        conn.commit()
        return True

    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False

    except Exception as e:
        conn.rollback()
        print("Signup error:", e)
        return False

    finally:
        cur.close()
        conn.close()

# ---------------- LOGIN ----------------

def login(username: str, password: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE username=%s AND password_hash=%s",
        (username, hash_password(password))
    )

    row = cur.fetchone()

    cur.close()
    conn.close()
    return row

# ---------------- USER EXISTS ----------------

def user_exists(username: str) -> bool:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT 1 FROM users WHERE username=%s",
        (username,)
    )

    exists = cur.fetchone() is not None

    cur.close()
    conn.close()
    return exists
