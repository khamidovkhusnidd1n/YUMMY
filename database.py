import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_file):
        self.conn = sqlite3.connect(db_file)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name_uz TEXT,
                name_ru TEXT,
                name_en TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT,
                price INTEGER,
                image TEXT,
                is_available INTEGER DEFAULT 1,
                FOREIGN KEY (category_id) REFERENCES categories (id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS media_cache (
                file_path TEXT PRIMARY KEY,
                file_id TEXT
            )
        """)
        self.conn.commit()

    def add_user(self, user_id, full_name, phone):
        # Update user info but don't overwrite language if it exists
        self.cursor.execute("INSERT INTO users (user_id, full_name, phone) VALUES (?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET full_name=excluded.full_name, phone=excluded.phone", 
                            (user_id, full_name, phone))
        self.conn.commit()

    def set_user_lang(self, user_id, lang):
        self.cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
        self.conn.commit()

    def get_user_lang(self, user_id):
        res = self.cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return res[0] if res else 'uz'

    def create_order(self, user_id, items, total_price, location=None):
        self.cursor.execute("INSERT INTO orders (user_id, items, total_price, location, created_at) VALUES (?, ?, ?, ?, ?)",
                            (user_id, items, total_price, location, datetime.now()))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_order(self, order_id):
        return self.cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()

    def update_order_status(self, order_id, status):
        self.cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        self.conn.commit()

    def get_stats(self):
        # Total Stats
        total_orders = self.cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'").fetchone()[0]
        total_revenue = self.cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'completed'").fetchone()[0] or 0
        return total_orders, total_revenue

    def get_daily_stats(self):
        # Stats for today
        today = datetime.now().strftime('%Y-%m-%d')
        orders = self.cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed' AND date(created_at) = ?", (today,)).fetchone()[0]
        revenue = self.cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'completed' AND date(created_at) = ?", (today,)).fetchone()[0] or 0
        return orders, revenue

    def get_file_id(self, file_path):
        res = self.cursor.execute("SELECT file_id FROM media_cache WHERE file_path = ?", (file_path,)).fetchone()
        return res[0] if res else None

    def set_file_id(self, file_path, file_id):
        self.cursor.execute("INSERT OR REPLACE INTO media_cache (file_path, file_id) VALUES (?, ?)", (file_path, file_id))
        self.conn.commit()

    def get_all_orders(self):
        return self.cursor.execute("SELECT order_id, user_id, items, total_price, status, location, created_at FROM orders").fetchall()

    def get_top_products(self):
        # This is a bit complex as items are stored as a string. 
        # For a truly 'sale-ready' bot, we should have an order_items table.
        # For now, we'll do a simple text-based count or suggest refactoring.
        # Let's assume we want to see the most frequent order strings for now.
        return self.cursor.execute("""
            SELECT items, COUNT(*) as count 
            FROM orders 
            WHERE status = 'completed' 
            GROUP BY items 
            ORDER BY count DESC 
            LIMIT 5
        """).fetchall()

    def get_top_customers(self):
        return self.cursor.execute("""
            SELECT u.full_name, u.phone, SUM(o.total_price) as total_spent
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE o.status = 'completed'
            GROUP BY o.user_id
            ORDER BY total_spent DESC
            LIMIT 5
        """).fetchall()

    def get_revenue_by_period(self, days=30):
        return self.cursor.execute("""
            SELECT date(created_at) as date, SUM(total_price) as revenue
            FROM orders
            WHERE status = 'completed' AND created_at >= date('now', ?)
            GROUP BY date
            ORDER BY date ASC
        """, (f'-{days} days',)).fetchall()

    # Fixing the accidentally removed users and orders tables
    def _create_users_table(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                phone TEXT,
                lang TEXT DEFAULT 'uz'
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                items TEXT,
                total_price INTEGER,
                status TEXT DEFAULT 'pending',
                location TEXT,
                created_at TIMESTAMP
            )
        """)
        self.conn.commit()

db = Database("yummy_bot.db")
db._create_users_table()
