import sqlite3

conn = sqlite3.connect('yummy_bot.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN lang TEXT DEFAULT 'uz'")
    conn.commit()
    print("SUCCESS: 'lang' column added!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("WARNING: 'lang' column already exists.")
    else:
        print(f"ERROR: {e}")
finally:
    conn.close()
