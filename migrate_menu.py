from database import db
from menu import MENU

def migrate():
    print("Migratsiya boshlandi...")
    
    # Clear existing data to avoid duplicates if run multiple times
    db.cursor.execute("DELETE FROM products")
    db.cursor.execute("DELETE FROM categories")
    db.cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('products', 'categories')")
    db.conn.commit()

    for cat_name, items in MENU.items():
        # Add category
        # Since we don't have separate translations for categories in menu.py, 
        # we'll use the same name for all languages for now.
        db.cursor.execute("""
            INSERT INTO categories (name_uz, name_ru, name_en) 
            VALUES (?, ?, ?)
        """, (cat_name, cat_name, cat_name))
        cat_id = db.cursor.lastrowid
        
        for item in items:
            db.cursor.execute("""
                INSERT INTO products (category_id, name, price, image) 
                VALUES (?, ?, ?, ?)
            """, (cat_id, item['name'], item['price'], item['image']))
            
    db.conn.commit()
    print("Migratsiya muvaffaqiyatli yakunlandi! [OK]")

if __name__ == "__main__":
    migrate()
