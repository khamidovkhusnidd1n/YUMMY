import sqlite3
import json
import os
import subprocess

def publish_menu():
    try:
        conn = sqlite3.connect('yummy_bot.db')
        cur = conn.cursor()
        
        # Fetch categories
        cur.execute("SELECT id, name_uz, name_ru, name_en FROM categories")
        categories = cur.fetchall()
        
        menu_data = {}
        dynamic_cats = {'uz': {}, 'ru': {}, 'en': {}}
        
        for cat_id, name_uz, name_ru, name_en in categories:
            # We use name_uz as the primary key for MENU_DATA to match existing templates
            # But the user might have different names in DB. 
            # Let's use name_uz.
            cat_key = name_uz
            
            # Store translations for categories
            dynamic_cats['uz'][cat_key] = name_uz
            dynamic_cats['ru'][cat_key] = name_ru
            dynamic_cats['en'][cat_key] = name_en
            
            # Fetch products for this category
            cur.execute("SELECT name, price, image FROM products WHERE category_id = ? AND is_available = 1", (cat_id,))
            products = cur.fetchall()
            
            menu_data[cat_key] = []
            for p_name, p_price, p_image in products:
                menu_data[cat_key].append({
                    "n": p_name,
                    "p": p_price,
                    "i": p_image
                })
        
        conn.close()
        
        # Generate JS content
        js_content = f"""
// Auto-generated menu data
window.DYNAMIC_MENU_DATA = {json.dumps(menu_data, ensure_ascii=False, indent=4)};
window.DYNAMIC_CATS = {json.dumps(dynamic_cats, ensure_ascii=False, indent=4)};
"""
        
        # Write to menu_data.js
        with open('menu_data.js', 'w', encoding='utf-8') as f:
            f.write(js_content)
            
        # Also, let's update index.html to make sure it includes menu_data.js
        with open('index.html', 'r', encoding='utf-8') as f:
            index_content = f.read()
            
        if 'src="menu_data.js"' not in index_content:
            # Insert before the first <script> that contains Telegram WebApp
            new_content = index_content.replace(
                '<script src="https://telegram.org/js/telegram-web-app.js"></script>',
                '<script src="menu_data.js?v=' + str(os.path.getmtime('yummy_bot.db')) + '"></script>\n    <script src="https://telegram.org/js/telegram-web-app.js"></script>'
            )
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(new_content)
        else:
            # Just update the version to bust cache
            import re
            new_content = re.sub(r'src="menu_data\.js\?v=[^"]+"', f'src="menu_data.js?v={os.path.getmtime("yummy_bot.db")}"', index_content)
            with open('index.html', 'w', encoding='utf-8') as f:
                f.write(new_content)

        # Git push changes
        subprocess.run(["git", "add", "menu_data.js", "index.html", "images/products/*"], capture_output=True)
        subprocess.run(["git", "commit", "-m", "Update menu from admin panel"], capture_output=True)
        # Push to both main and master to be safe
        subprocess.run(["git", "push", "origin", "HEAD:main", "--force"], capture_output=True)
        subprocess.run(["git", "push", "origin", "HEAD:master", "--force"], capture_output=True)
        
        return True
    except Exception as e:
        print(f"Publish error: {e}")
        return False

if __name__ == "__main__":
    publish_menu()
