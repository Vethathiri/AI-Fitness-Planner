import psycopg2
import streamlit as st

# ---------------- CONNECTION ----------------

def get_connection():
    return psycopg2.connect(
        host=st.secrets["DB_HOST"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"],
        port=st.secrets["DB_PORT"],
        sslmode="require"
    )

# ---------------- USERS ----------------

def delete_user(uid):
    conn = get_connection()
    cur = conn.cursor()

    tables = ["plans", "plan_versions", "chats", "progress", "preferences"]

    for t in tables:
        cur.execute(f"DELETE FROM {t} WHERE user_id=%s", (uid,))

    cur.execute("DELETE FROM users WHERE id=%s", (uid,))
    conn.commit()

    cur.close()
    conn.close()

# ---------------- PLANS ----------------

def get_plan_history(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, week, plan, timestamp
        FROM plans
        WHERE user_id=%s
        ORDER BY week DESC
    """, (user_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows

def delete_plan(plan_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT user_id, week FROM plans WHERE id=%s", (plan_id,))
    row = cur.fetchone()

    if row:
        user_id, week = row
        cur.execute("DELETE FROM plans WHERE id=%s", (plan_id,))
        cur.execute(
            "DELETE FROM progress WHERE user_id=%s AND week=%s",
            (user_id, week)
        )
        conn.commit()

    cur.close()
    conn.close()

# ---------------- USERS LIST ----------------

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, username FROM users ORDER BY username")
    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows

# ---------------- PROFILE ----------------

def get_user_profile(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT age, height, weight, state, city, goal,
               diet, workout_place, budget
        FROM user_profile
        WHERE user_id=%s
    """, (user_id,))

    row = cur.fetchone()

    cur.close()
    conn.close()
    return row

def upsert_user_profile(
    user_id, age, height, weight,
    state, city, goal, diet, workout_place, budget
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO user_profile
        (user_id, age, height, weight, state, city,
         goal, diet, workout_place, budget)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            age=EXCLUDED.age,
            height=EXCLUDED.height,
            weight=EXCLUDED.weight,
            state=EXCLUDED.state,
            city=EXCLUDED.city,
            goal=EXCLUDED.goal,
            diet=EXCLUDED.diet,
            workout_place=EXCLUDED.workout_place,
            budget=EXCLUDED.budget
    """, (
        user_id, age, height, weight,
        state, city, goal, diet, workout_place, budget
    ))

    conn.commit()
    cur.close()
    conn.close()

# ---------------- PROGRESS ----------------

def get_user_progress(user_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT week, weight, difficulty, timestamp
        FROM progress
        WHERE user_id=%s
        ORDER BY week ASC
    """, (user_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()
    return rows


