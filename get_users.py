import sqlite3
import json
import sys
from datetime import datetime, timedelta

# Force UTF-8 for Windows console
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def get_active_users():
    conn = sqlite3.connect('yummy_bot.db')
    cursor = conn.cursor()
    
    # Get users who placed orders in the last 7 days to be safe
    query = """
    SELECT DISTINCT 
        u.user_id, 
        u.full_name, 
        u.username, 
        u.phone, 
        MAX(o.created_at) as last_activity
    FROM orders o
    JOIN users u ON o.user_id = u.user_id
    WHERE o.created_at >= date('now', '-7 days')
    GROUP BY u.user_id
    ORDER BY last_activity DESC
    """
    
    try:
        rows = cursor.execute(query).fetchall()
        print(f"Topildi: {len(rows)} ta faol foydalanuvchi (oxirgi 7 kun).\n")
        
        for row in rows:
            uid, name, username, phone, last_time = row
            print(f"Ism: {name}")
            print(f"Username: @{username}" if username and username != 'Noma\'lum' else "Username: Yo'q")
            print(f"Tel: {phone}")
            print(f"Oxirgi buyurtma: {last_time}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Xatolik: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    get_active_users()
