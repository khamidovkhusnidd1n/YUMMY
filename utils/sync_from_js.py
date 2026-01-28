import re
import json
import sqlite3
import os

def import_menu_from_js():
    file_path = 'menu_data.js'
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find JSON blocks
    # We look for something like window.DYNAMIC_MENU_DATA = { ... };
    menu_pattern = r'window\.DYNAMIC_MENU_DATA\s*=\s*(\{.*?\});'
    cats_pattern = r'window\.DYNAMIC_CATS\s*=\s*(\{.*?\});'
    
    menu_match = re.search(menu_pattern, content, re.DOTALL)
    cats_match = re.search(cats_pattern, content, re.DOTALL)
    
    if not menu_match:
        print("Error: Could not find DYNAMIC_MENU_DATA in menu_data.js")
        return
    
    # Process Menu Data JSON
    menu_str = menu_match.group(1)
    # Basic cleanup for JS to JSON (not perfect but works for this specific file)
    # If keys are not quoted, we should quote them, but here they are quoted.
    try:
        menu_data = json.loads(menu_str)
    except Exception as e:
        print(f"Error parsing Menu JSON: {e}")
        # Fallback: simple cleanup
        menu_str_clean = re.sub(r',\s*([}\]])', r'\1', menu_str) # Trailing commas
        try:
            menu_data = json.loads(menu_str_clean)
        except:
            print("Failed to parse Menu data even after cleanup.")
            return

    # Process Cats Data JSON
    if cats_match:
        cats_str = cats_match.group(1)
        try:
            cats_data = json.loads(cats_str)
        except:
            cats_str_clean = re.sub(r',\s*([}\]])', r'\1', cats_str)
            cats_data = json.loads(cats_str_clean)
    else:
        cats_data = {'uz': {}, 'ru': {}, 'en': {}}

    conn = sqlite3.connect('yummy_bot.db')
    cur = conn.cursor()
    
    # Clear tables to start fresh
    cur.execute("DELETE FROM products")
    cur.execute("DELETE FROM categories")
    cur.execute("DELETE FROM sqlite_sequence WHERE name='products' OR name='categories'")
    
    for cat_name, items in menu_data.items():
        # Translations
        name_uz = cats_data.get('uz', {}).get(cat_name, cat_name)
        name_ru = cats_data.get('ru', {}).get(cat_name, cat_name)
        name_en = cats_data.get('en', {}).get(cat_name, cat_name)
        
        cur.execute("INSERT INTO categories (name_uz, name_ru, name_en) VALUES (?, ?, ?)", 
                    (name_uz, name_ru, name_en))
        cat_id = cur.lastrowid
        
        for item in items:
            cur.execute("INSERT INTO products (category_id, name, price, image) VALUES (?, ?, ?, ?)",
                        (cat_id, item['n'], item['p'], item['i']))
            
    conn.commit()
    conn.close()
    print(f"Successfully imported {len(menu_data)} categories from menu_data.js to yummy_bot.db")

if __name__ == "__main__":
    import_menu_from_js()
