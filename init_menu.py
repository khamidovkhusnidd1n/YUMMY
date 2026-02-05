"""
Hardcoded category and product initializer.
This script directly inserts default menu data into the database,
bypassing the need to parse menu_data.js.
"""
import sqlite3
import os

MENU_DATA = {
    "🔥 Specials": [
        {"n": "Kfc BURGER (+0.25 Cola)", "p": 33000, "i": "images/image2/kfc_burger.jpg"},
        {"n": "Kfc HAGGI (+0.25 Cola)", "p": 38000, "i": "images/image2/kfc_haggi_cola.jpg"}
    ],
    "🍔 MAZZA": [
        {"n": "MAZZA (Kichik)", "p": 15000, "i": "images/mazza.jpg"},
        {"n": "MAZZA (Katta)", "p": 30000, "i": "images/mazza.jpg"}
    ],
    "🌯 Lavash": [
        {"n": "Standart", "p": 30000, "i": "images/lavash.jpg"},
        {"n": "Pishloqli", "p": 35000, "i": "images/image2/images3/lavash_cheese.jpg"},
        {"n": "Big", "p": 40000, "i": "images/image2/images3/lavash_big.jpg"},
        {"n": "Big pishloq", "p": 45000, "i": "images/image2/images3/lavash_cheese.jpg"}
    ],
    "🍔 Burger": [
        {"n": "Gamburger", "p": 28000, "i": "images/burger.jpg"},
        {"n": "Chizburger", "p": 33000, "i": "images/image2/images3/cheeseburger.jpg"},
        {"n": "Double", "p": 35000, "i": "images/image2/images3/double_burger.jpg"},
        {"n": "Double chiz", "p": 40000, "i": "images/image2/images3/double_cheese.jpg"}
    ],
    "🥙 Doner": [
        {"n": "Standart Doner", "p": 25000, "i": "images/image2/donar.jpg"},
        {"n": "Katta Doner", "p": 30000, "i": "images/image2/images3/donerbig.jpg"},
        {"n": "Pishloqli Doner", "p": 35000, "i": "images/image2/donar.jpg"}
    ],
    "🍗 KFC": [
        {"n": "File strips", "p": 90000, "i": "images/image2/images3/Fillet_strips.jpg"},
        {"n": "Qanot", "p": 85000, "i": "images/image2/images3/wings.jpg"},
        {"n": "Lunch box", "p": 30000, "i": "images/image2/images3/lunch_box.jpg"},
        {"n": "Kfc xaggi", "p": 30000, "i": "images/image2/images3/KFC_xaggi.jpg"}
    ],
    "🌭 Xot-dog": [
        {"n": "Mini", "p": 10000, "i": "images/image2/hot_dog.jpg"},
        {"n": "Twins", "p": 17000, "i": "images/image2/images3/twins.jpg"},
        {"n": "Big (45sm)", "p": 22000, "i": "images/image2/images3/hotdogbig.jpg"},
        {"n": "Super (45sm)", "p": 25000, "i": "images/image2/hot_dog.jpg"},
        {"n": "Canada (45sm)", "p": 25000, "i": "images/hotdog_canada.jpg"}
    ],
    "🥪 Xaggi": [
        {"n": "Standart", "p": 35000, "i": "images/image2/xaggi.jpg"},
        {"n": "Big", "p": 45000, "i": "images/image2/images3/xaggi_big.jpg"},
        {"n": "Xot let", "p": 28000, "i": "images/image2/images3/xaggi.jpg"}
    ],
    "🍗 Naggets": [
        {"n": "Naggets", "p": 22000, "i": "images/naggets.jpg"},
        {"n": "Naggets mini", "p": 11000, "i": "images/naggets.jpg"}
    ],
    "🧀 Pishloqli yostiqchalar": [
        {"n": "Yostiqchalar", "p": 28000, "i": "images/pishloqli.jpg"},
        {"n": "Yostiqchalar mini", "p": 14000, "i": "images/pishloqli.jpg"}
    ],
    "🥪 Klab sandwich": [
        {"n": "Standart", "p": 35000, "i": "images/sandwich.jpg"}
    ],
    "🍟 Fri": [
        {"n": "Standart", "p": 15000, "i": "images/fri.jpg"},
        {"n": "Big", "p": 17000, "i": "images/image2/images3/fribig.jpg"}
    ],
    "🥟 Somsa": [
        {"n": "Go'shtli", "p": 10000, "i": "images/somsa.jpg"},
        {"n": "Pishloqli tovuq", "p": 7000, "i": "images/image2/images3/chickensomsa.jpg"},
        {"n": "Ko'k", "p": 5000, "i": "images/image2/images3/koksomsa.jpg"},
        {"n": "Kartoshka", "p": 5000, "i": "images/image2/images3/kartoshkalisomsa.jpg"}
    ],
    "☕️ Ichimliklar": [
        {"n": "Choy", "p": 3000, "i": "images/image2/tea.jpg"},
        {"n": "Kofe", "p": 5000, "i": "images/image2/coffee.jpg"},
        {"n": "Kofe (Big)", "p": 7000, "i": "images/image2/coffee.jpg"},
        {"n": "Choy mevali", "p": 10000, "i": "images/image2/tea_via_fruits.jpg"}
    ],
    "🍹 Cocktails": [
        {"n": "Tropic", "p": 15000, "i": "images/image2/tropic.jpg"},
        {"n": "Moxito", "p": 15000, "i": "images/image2/moxito.jpg"},
        {"n": "O'rmon mevalari", "p": 15000, "i": "images/image2/forest_fruits.jpg"}
    ],
    "🥫 Souslar": [
        {"n": "Sous", "p": 4000, "i": "images/image2/sous.jpg"}
    ]
}

def init_menu():
    db_path = "yummy_bot.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Clear existing
    cur.execute("DELETE FROM products")
    cur.execute("DELETE FROM categories")
    try:
        cur.execute("DELETE FROM sqlite_sequence WHERE name='products' OR name='categories'")
    except:
        pass
    
    for cat_name, items in MENU_DATA.items():
        cur.execute("INSERT INTO categories (name_uz, name_ru, name_en) VALUES (?, ?, ?)", 
                    (cat_name, cat_name, cat_name))
        cat_id = cur.lastrowid
        
        for item in items:
            cur.execute("INSERT INTO products (category_id, name, price, image) VALUES (?, ?, ?, ?)",
                        (cat_id, item['n'], item['p'], item['i']))
    
    conn.commit()
    conn.close()
    print(f"Menu initialized: {len(MENU_DATA)} categories added.")

if __name__ == "__main__":
    init_menu()
