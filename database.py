import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT")
)

conn.autocommit = True


def get_cursor():
    return conn.cursor()


def delete_user(uid):
    cur=get_cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (uid,))

    tables = ["plans", "plan_versions", "chats", "progress", "preferences"]
    for t in tables:
        cur.execute(f"DELETE FROM {t} WHERE user_id=%s", (uid,))

def get_plan_history(user_id):
    cur=get_cursor()
    cur.execute(
        """
        SELECT id,week,plan, timestamp
        FROM plans
        WHERE user_id=%s
        ORDER BY week DESC
        """,
        (user_id,)
    )
    return cur.fetchall()

def get_all_users():
    cur=get_cursor()
    cur.execute("SELECT id, username FROM users ORDER BY username")
    return cur.fetchall()

def get_user_profile(user_id):
    cur=get_cursor()
    cur.execute(
        "SELECT age, height, weight, state, city, goal, diet, workout_place, budget "
        "FROM user_profile WHERE user_id=%s",
        (user_id,)
    )
    return cur.fetchone()

def upsert_user_profile(user_id, age, height, weight, state, city, goal, diet, workout_place, budget):
    cur=get_cursor()
    cur.execute("""
        INSERT INTO user_profile
        (user_id, age, height, weight, state, city, goal, diet, workout_place, budget)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT(user_id) DO UPDATE SET
            age=excluded.age,
            height=excluded.height,
            weight=excluded.weight,
            state=excluded.state,
            city=excluded.city,
            goal=excluded.goal,
            diet=excluded.diet,
            workout_place=excluded.workout_place,
            budget=excluded.budget
    """, (user_id, age, height, weight, state, city, goal, diet, workout_place, budget))

def get_user_progress(user_id):
    cur=get_cursor()
    cur.execute("""
        SELECT week,weight, difficulty, timestamp
        FROM progress
        WHERE user_id=%s
        ORDER BY timestamp ASC
    """, (user_id,))
    return cur.fetchall()

def delete_plan(plan_id):
    cur=get_cursor()
    cur.execute(
        "SELECT user_id, week FROM plans WHERE id=%s",
        (plan_id,)
    )
    row = cur.fetchone()

    if not row:
        return

    user_id, week = row

    # Delete plan
    cur.execute("DELETE FROM plans WHERE id=%s", (plan_id,))

    # Delete corresponding progress
    cur.execute(
        "DELETE FROM progress WHERE user_id=%s AND week=%s",
        (user_id, week)
    )


    
