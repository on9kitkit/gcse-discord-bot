import sqlite3

# 🔌 Connect database FIRST
conn = sqlite3.connect("data.db")
cursor = conn.cursor()

# 🧱 Create tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    xp INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_stats (
    user_id INTEGER PRIMARY KEY,
    total_answers INTEGER,
    bio_count INTEGER,
    phy_count INTEGER,
    eng_count INTEGER
)
""")

conn.commit()


# 🎮 XP SYSTEM
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


# 🏆 LEADERBOARD
def get_leaderboard():
    cursor.execute("SELECT user_id, xp FROM users ORDER BY xp DESC LIMIT 5")
    return cursor.fetchall()


# 🧠 MEMORY SYSTEM
def update_stats(user_id, subject):
    cursor.execute("SELECT * FROM user_stats WHERE user_id=?", (user_id,))
    result = cursor.fetchone()

    if result is None:
        total = 1
        bio = phy = eng = 0
    else:
        total = result[1] + 1
        bio = result[2]
        phy = result[3]
        eng = result[4]

    if subject == "bio":
        bio += 1
    elif subject == "phy":
        phy += 1
    elif subject == "eng":
        eng += 1

    cursor.execute("""
    INSERT OR REPLACE INTO user_stats (user_id, total_answers, bio_count, phy_count, eng_count)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, total, bio, phy, eng))

    conn.commit()
