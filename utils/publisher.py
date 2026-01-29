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
        
        with open('menu_data.js', 'w', encoding='utf-8') as f:
            f.write(js_content)
            
        # We don't need to update index.html anymore because it now has 
        # a dynamic script tag that handles cache busting automatically.

        # Git push changes - safely
        try:
            # Add updated files
            subprocess.run(["git", "add", "menu_data.js", "index.html"], capture_output=True, check=False)
            # Check if there are products to add
            if os.path.exists("images/products"):
                subprocess.run(["git", "add", "images/products/*"], capture_output=True, check=False)
            
            # Commit
            subprocess.run(["git", "commit", "-m", "Update menu data [Auto-sync]"], capture_output=True, check=False)
            
            # Push to main
            res = subprocess.run(["git", "push", "origin", "main", "--force"], capture_output=True, check=False)
            
            if res.returncode != 0:
                print(f"Git push failed: {res.stderr.decode()}")
        except Exception as ge:
            print(f"Git operations failed: {ge}")

        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Publish error: {e}")
        return False

if __name__ == "__main__":
    publish_menu()
