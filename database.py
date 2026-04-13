import sqlite3

conn = sqlite3.connect("data.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER
)
""")

conn.commit()


def add_xp(user_id, amount):
    cursor.execute("SELECT xp FROM users WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if result is None:
        xp = amount
        cursor.execute("INSERT INTO users (user_id, xp) VALUES (?, ?)", (user_id, xp))
    else:
        xp = result[0] + amount
        cursor.execute("UPDATE users SET xp=? WHERE user_id=?", (xp, user_id))

    conn.commit()
    return xp


def get_leaderboard():
    cursor.execute("SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 5")
    return cursor.fetchall()
