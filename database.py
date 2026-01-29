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
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                discount_percent INTEGER,
                is_active INTEGER DEFAULT 1,
                expiry_date TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
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
                promo_code TEXT,
                discount_amount INTEGER DEFAULT 0,
                method TEXT,
                location TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                role TEXT DEFAULT 'admin',
                permissions TEXT DEFAULT '',
                is_active INTEGER DEFAULT 1,
                added_at TIMESTAMP
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                user_id INTEGER PRIMARY KEY,
                items TEXT,
                updated_at TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_user(self, user_id, full_name, username, phone):
        self.cursor.execute("INSERT INTO users (user_id, full_name, username, phone) VALUES (?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET full_name=excluded.full_name, username=excluded.username, phone=excluded.phone", 
                            (user_id, full_name, username, phone))
        self.conn.commit()

    def get_user(self, user_id):
        return self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()

    def set_user_lang(self, user_id, lang):
        self.cursor.execute(
            "INSERT INTO users (user_id, lang) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET lang=excluded.lang",
            (user_id, lang)
        )
        self.conn.commit()

    def get_user_lang(self, user_id):
        res = self.cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,)).fetchone()
        return res[0] if res else 'uz'

    def create_order(self, user_id, items, total_price, promo_code=None, discount_amount=0, method=None, location=None):
        self.cursor.execute("""
            INSERT INTO orders (user_id, items, total_price, promo_code, discount_amount, method, location, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, items, total_price, promo_code, discount_amount, method, location, datetime.now()))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_order(self, order_id):
        return self.cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,)).fetchone()

    def update_order_status(self, order_id, status):
        self.cursor.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
        self.conn.commit()

    def get_stats(self):
        total_orders = self.cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'").fetchone()[0]
        total_revenue = self.cursor.execute("SELECT SUM(total_price) FROM orders WHERE status = 'completed'").fetchone()[0] or 0
        return total_orders, total_revenue

    def get_daily_stats(self):
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
        return self.cursor.execute("""
            SELECT o.order_id, o.user_id, u.full_name, u.username, u.phone, 
                   o.items, o.total_price, o.promo_code, o.discount_amount, 
                   o.method, o.location, o.status, o.created_at
            FROM orders o
            LEFT JOIN users u ON o.user_id = u.user_id
        """).fetchall()

    def get_top_products(self):
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

    def get_peak_hours(self):
        """Returns top 3 peak hours for orders"""
        return self.cursor.execute("""
            SELECT strftime('%H:00', created_at) as hour, COUNT(*) as count 
            FROM orders 
            WHERE status = 'completed'
            GROUP BY hour 
            ORDER BY count DESC 
            LIMIT 3
        """).fetchall()

    def get_revenue_by_period(self, days=30):
        return self.cursor.execute("""
            SELECT date(created_at) as date, SUM(total_price) as revenue
            FROM orders
            WHERE status = 'completed' AND created_at >= date('now', ?)
            GROUP BY date
            ORDER BY date ASC
        """, (f'-{days} days',)).fetchall()

    def _create_users_table(self):
        # Already handled in create_tables
        pass

    # --- Product Management ---
    def add_product(self, category_id, name, price, image):
        self.cursor.execute("INSERT INTO products (category_id, name, price, image) VALUES (?, ?, ?, ?)",
                            (category_id, name, price, image))
        self.conn.commit()

    def update_product_price(self, product_id, new_price):
        self.cursor.execute("UPDATE products SET price = ? WHERE id = ?", (new_price, product_id))
        self.conn.commit()

    def delete_product(self, product_id):
        self.cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()

    def toggle_product_availability(self, product_id, is_available):
        self.cursor.execute("UPDATE products SET is_available = ? WHERE id = ?", (is_available, product_id))
        self.conn.commit()

    def get_products_by_category(self, category_id):
        return self.cursor.execute("SELECT * FROM products WHERE category_id = ?", (category_id,)).fetchall()

    def get_all_categories(self):
        return self.cursor.execute("SELECT * FROM categories").fetchall()

    def get_category_by_name(self, name):
        return self.cursor.execute("SELECT * FROM categories WHERE name_uz = ? OR name_ru = ? OR name_en = ?", (name, name, name)).fetchone()

    # --- Promo Codes ---
    def create_promo_code(self, code, discount_percent, expiry_date=None):
        self.cursor.execute("INSERT INTO promo_codes (code, discount_percent, expiry_date) VALUES (?, ?, ?)",
                            (code, discount_percent, expiry_date))
        self.conn.commit()

    def get_promo_code(self, code):
        return self.cursor.execute("SELECT * FROM promo_codes WHERE code = ? AND is_active = 1", (code,)).fetchone()

    def delete_promo_code(self, code_id):
        self.cursor.execute("DELETE FROM promo_codes WHERE id = ?", (code_id,))
        self.conn.commit()

    def get_all_promo_codes(self):
        return self.cursor.execute("SELECT * FROM promo_codes").fetchall()

    # --- Admin Management ---
    def add_admin(self, user_id, role='admin', permissions=''):
        self.cursor.execute("INSERT OR REPLACE INTO admins (user_id, role, permissions, is_active, added_at) VALUES (?, ?, ?, 1, ?)",
                            (user_id, role, permissions, datetime.now()))
        self.conn.commit()

    def remove_admin(self, user_id):
        self.cursor.execute("UPDATE admins SET is_active = 0 WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def get_admin(self, user_id, active_only=True):
        query = "SELECT * FROM admins WHERE user_id = ?"
        if active_only:
            query += " AND is_active = 1"
        return self.cursor.execute(query, (user_id,)).fetchone()

    def get_all_admins(self):
        return self.cursor.execute("SELECT * FROM admins").fetchall()

    def update_admin_role(self, user_id, role):
        self.cursor.execute("UPDATE admins SET role = ? WHERE user_id = ?", (role, user_id))
        self.conn.commit()

    def update_admin_permissions(self, user_id, permissions):
        self.cursor.execute("UPDATE admins SET permissions = ? WHERE user_id = ?", (permissions, user_id))
        self.conn.commit()

    def is_admin(self, user_id):
        res = self.cursor.execute("SELECT 1 FROM admins WHERE user_id = ?", (user_id,)).fetchone()
        return res is not None

    def has_permission(self, user_id, permission):
        admin = self.get_admin(user_id)
        if not admin: return False
        if admin[1] == 'super_admin': return True
        return permission in admin[2].split(',')

    def get_all_users(self):
        return self.cursor.execute("SELECT user_id FROM users").fetchall()

    # --- Cart Management ---
    def update_cart(self, user_id, items_json):
        self.cursor.execute("INSERT OR REPLACE INTO cart (user_id, items, updated_at) VALUES (?, ?, ?)",
                            (user_id, items_json, datetime.now()))
        self.conn.commit()

    def get_cart(self, user_id):
        res = self.cursor.execute("SELECT items FROM cart WHERE user_id = ?", (user_id,)).fetchone()
        return res[0] if res else None

    def clear_cart(self, user_id):
        self.cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        self.conn.commit()

db = Database("yummy_bot.db")
db.create_tables()
