import sqlite3

DB_NAME = "bot.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            is_allowed INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0
        )
    """)

    # Add is_blocked column if the old database does not have it
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]

    if "is_blocked" not in columns:
        cursor.execute(
            "ALTER TABLE users ADD COLUMN is_blocked INTEGER DEFAULT 0"
        )

    conn.commit()
    conn.close()


def add_user(
    user_id,
    username="",
    first_name="",
    is_allowed=0,
    is_admin=0
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users
        (
            user_id,
            username,
            first_name,
            is_allowed,
            is_admin,
            is_blocked
        )
        VALUES (?, ?, ?, ?, ?, 0)

        ON CONFLICT(user_id) DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name,
            is_allowed = excluded.is_allowed,
            is_admin = excluded.is_admin
    """, (
        user_id,
        username,
        first_name,
        is_allowed,
        is_admin
    ))

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id,
            username,
            first_name,
            is_allowed,
            is_admin,
            is_blocked
        FROM users
        WHERE user_id = ?
    """, (user_id,))

    user = cursor.fetchone()

    conn.close()

    return user


def set_allowed(user_id, allowed):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET is_allowed = ?
        WHERE user_id = ?
    """, (
        1 if allowed else 0,
        user_id
    ))

    conn.commit()
    conn.close()


def set_blocked(user_id, blocked):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users
        SET is_blocked = ?
        WHERE user_id = ?
    """, (
        1 if blocked else 0,
        user_id
    ))

    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            user_id,
            username,
            first_name,
            is_allowed,
            is_admin,
            is_blocked
        FROM users
        ORDER BY user_id
    """)

    users = cursor.fetchall()

    conn.close()

    return users