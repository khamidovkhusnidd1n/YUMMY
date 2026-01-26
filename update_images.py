import sqlite3

def update_lavash_images():
    conn = sqlite3.connect("yummy_bot.db")
    cursor = conn.cursor()
    
    lavash_img = "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=600&h=600&fit=crop"
    
    # Update products in Lavash category
    # First, find the Lavash category ID
    cursor.execute("SELECT id FROM categories WHERE name_uz LIKE '%Lavash%'")
    cat_res = cursor.fetchone()
    
    if cat_res:
        cat_id = cat_res[0]
        cursor.execute("UPDATE products SET image = ? WHERE category_id = ?", (lavash_img, cat_id))
        conn.commit()
        print(f"Lavash taomlari uchun rasm yangilandi! Cat ID: {cat_id}")
    else:
        print("Lavash kategoriyasi topilmadi.")
        
    conn.close()

if __name__ == "__main__":
    update_lavash_images()
