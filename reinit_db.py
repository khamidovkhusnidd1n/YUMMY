import sqlite3

def reinit():
    conn = sqlite3.connect("yummy_bot.db")
    cursor = conn.cursor()

    # Clear old data
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM categories")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('products', 'categories')")

    # Categories
    cats = [
        ("🌯 Lavash", "🌯 Лаваш", "🌯 Lavash"),
        ("🍔 Burger", "🍔 Бургер", "🍔 Burger"),
        ("🥙 Doner", "🥙 Донер", "🥙 Doner"),
        ("🍗 KFC", "🍗 KFC", "🍗 KFC"),
        ("🌭 Xot-dog", "🌭 Хот-дог", "🌭 Hot-dog"),
        ("🥪 Xaggi", "🥪 Хагги", "🥪 Haggi"),
        ("🍗 Naggets", "🍗 Наггетсы", "🍗 Nuggets"),
        ("🧀 Pishloqli yostiqchalar", "🧀 Сырные", "🧀 Cheese pods"),
        ("🥪 Klab sandwich", "🥪 Клаб", "🥪 Club"),
        ("🍟 Fri", "🍟 Фри", "🍟 Fries"),
        ("🥟 Somsa", "🥟 Сомса", "🥟 Somsa"),
        ("☕️ Ichimliklar", "☕️ Напитки", "☕️ Drinks"),
        ("🍹 Cocktails", "🍹 Коктейли", "🍹 Cocktails"),
        ("🔥 Specials", "🔥 Акции", "🔥 Specials"),
        ("🥫 Souslar", "🥫 Соусы", "🥫 Sauces")
    ]

    for uz, ru, en in cats:
        cursor.execute("INSERT INTO categories (name_uz, name_ru, name_en) VALUES (?, ?, ?)", (uz, ru, en))
    
    conn.commit()

    # Get category IDs
    cursor.execute("SELECT id, name_uz FROM categories")
    cat_ids = {name: id for id, name in cursor.fetchall()}

    # Products
    products = [
        # Lavash
        (cat_ids["🌯 Lavash"], "Standart", 30000, "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=600&h=600&fit=crop"),
        (cat_ids["🌯 Lavash"], "Pishloqli", 35000, "https://images.unsplash.com/photo-1547060640-5290b2bd497b?w=600&h=600&fit=crop"),
        (cat_ids["🌯 Lavash"], "Big", 40000, "https://images.unsplash.com/photo-1626700051175-6818013e1d4f?w=600&h=600&fit=crop"),
        (cat_ids["🌯 Lavash"], "Big pishloq", 45000, "https://images.unsplash.com/photo-1547060640-5290b2bd497b?w=600&h=600&fit=crop"),
        
        # Burger
        (cat_ids["🍔 Burger"], "Gamburger", 28000, "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=600&h=600&fit=crop"),
        (cat_ids["🍔 Burger"], "Chizburger", 33000, "https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=600&h=600&fit=crop"),
        (cat_ids["🍔 Burger"], "Double", 35000, "https://images.unsplash.com/photo-1606755962773-d324e0a13086?w=600&h=600&fit=crop"),
        (cat_ids["🍔 Burger"], "Double chiz", 40000, "https://images.unsplash.com/photo-1572802419224-296b0aeee0d9?w=600&h=600&fit=crop"),

        # Doner
        (cat_ids["🥙 Doner"], "Standart", 25000, "https://images.unsplash.com/photo-1561651823-34fed0225304?w=600&h=600&fit=crop"),
        (cat_ids["🥙 Doner"], "Big", 30000, "https://images.unsplash.com/photo-1529006557810-274b9b2fc783?w=600&h=600&fit=crop"),
        (cat_ids["🥙 Doner"], "Chiz", 35000, "https://images.unsplash.com/photo-1561651823-34fed0225304?w=600&h=600&fit=crop"),

        # KFC
        (cat_ids["🍗 KFC"], "File strips", 90000, "https://images.unsplash.com/photo-1562967914-6cbb04bac8cd?w=600&h=600&fit=crop"),
        (cat_ids["🍗 KFC"], "Qanot", 85000, "https://images.unsplash.com/photo-1606755456206-b25206cde27e?w=600&h=600&fit=crop"),
        (cat_ids["🍗 KFC"], "Lunch box", 30000, "https://images.unsplash.com/photo-1569058242253-92a9c73f49bc?w=600&h=600&fit=crop"),
        (cat_ids["🍗 KFC"], "Kfc xaggi", 30000, "https://images.unsplash.com/photo-1509482560494-4126f8225994?w=600&h=600&fit=crop"),

        # Xot-dog
        (cat_ids["🌭 Xot-dog"], "Mini", 10000, "https://images.unsplash.com/photo-1541214113241-21578d2d9b62?w=600&h=600&fit=crop"),
        (cat_ids["🌭 Xot-dog"], "Twins", 17000, "https://images.unsplash.com/photo-1594212699903-ec8a3eca50f5?w=600&h=600&fit=crop"),
        (cat_ids["🌭 Xot-dog"], "Big (45sm)", 22000, "https://images.unsplash.com/photo-1612392062631-94dd858cba88?w=600&h=600&fit=crop"),
        (cat_ids["🌭 Xot-dog"], "Super (45sm)", 25000, "https://images.unsplash.com/photo-1612392062631-94dd858cba88?w=600&h=600&fit=crop"),
        (cat_ids["🌭 Xot-dog"], "Canada (45sm)", 25000, "https://images.unsplash.com/photo-1612392062631-94dd858cba88?w=600&h=600&fit=crop"),

        # Xaggi
        (cat_ids["🥪 Xaggi"], "Standart", 35000, "https://images.unsplash.com/photo-1550507992-eb63ffee0847?w=600&h=600&fit=crop"),
        (cat_ids["🥪 Xaggi"], "Big", 45000, "https://images.unsplash.com/photo-1550507992-eb63ffee0847?w=600&h=600&fit=crop"),
        (cat_ids["🥪 Xaggi"], "Xot let", 28000, "https://images.unsplash.com/photo-1619860860774-1e2e17343432?w=600&h=600&fit=crop"),

        # Naggets
        (cat_ids["🍗 Naggets"], "Naggets", 22000, "https://images.unsplash.com/photo-1562967914-6cbb04bac8cd?w=600&h=600&fit=crop"),
        (cat_ids["🍗 Naggets"], "Naggets mini", 11000, "https://images.unsplash.com/photo-1562967914-6cbb04bac8cd?w=600&h=600&fit=crop"),

        # Pishloqli yostiqchalar
        (cat_ids["🧀 Pishloqli yostiqchalar"], "Yostiqchalar", 28000, "https://images.unsplash.com/photo-1548340748-6d2b7d7da280?w=600&h=600&fit=crop"),
        (cat_ids["🧀 Pishloqli yostiqchalar"], "Yostiqchalar mini", 14000, "https://images.unsplash.com/photo-1548340748-6d2b7d7da280?w=600&h=600&fit=crop"),

        # Klab sandwich
        (cat_ids["🥪 Klab sandwich"], "Standart", 35000, "https://images.unsplash.com/photo-1525351484163-7529414344d8?w=600&h=600&fit=crop"),

        # Fri
        (cat_ids["🍟 Fri"], "Standart", 15000, "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=600&h=600&fit=crop"),
        (cat_ids["🍟 Fri"], "Big", 17000, "https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=600&h=600&fit=crop"),

        # Somsa
        (cat_ids["🥟 Somsa"], "Go'shtli", 10000, "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&h=600&fit=crop"),
        (cat_ids["🥟 Somsa"], "Pishloqli tovuq", 7000, "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&h=600&fit=crop"),
        (cat_ids["🥟 Somsa"], "Ko'k", 5000, "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&h=600&fit=crop"),
        (cat_ids["🥟 Somsa"], "Kartoshka", 5000, "https://images.unsplash.com/photo-1601050690597-df0568f70950?w=600&h=600&fit=crop"),

        # Ichimliklar
        (cat_ids["☕️ Ichimliklar"], "Choy", 3000, "https://images.unsplash.com/photo-1544145945-f904253d0c7b?w=600&h=600&fit=crop"),
        (cat_ids["☕️ Ichimliklar"], "Kofe", 5000, "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&h=600&fit=crop"),
        (cat_ids["☕️ Ichimliklar"], "Kofe (Big)", 7000, "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=600&h=600&fit=crop"),
        (cat_ids["☕️ Ichimliklar"], "Choy mevali", 10000, "https://images.unsplash.com/photo-1520933906645-05999e103fe3?w=600&h=600&fit=crop"),

        # Cocktails
        (cat_ids["🍹 Cocktails"], "Tropic", 15000, "https://images.unsplash.com/photo-1513558111299-67ff41860975?w=600&h=600&fit=crop"),
        (cat_ids["🍹 Cocktails"], "Moxito", 15000, "https://images.unsplash.com/photo-1513558111299-67ff41860975?w=600&h=600&fit=crop"),
        (cat_ids["🍹 Cocktails"], "O'rmon mevalari", 15000, "https://images.unsplash.com/photo-1513558111299-67ff41860975?w=600&h=600&fit=crop"),

        # Specials
        (cat_ids["🔥 Specials"], "Kfc BURGER (+0.25 Cola)", 33000, "https://images.unsplash.com/photo-1551782450-a2132b4ba21d?w=600&h=600&fit=crop"),
        (cat_ids["🔥 Specials"], "Kfc HAGGI (+0.25 Cola)", 38000, "https://images.unsplash.com/photo-1509482560494-4126f8225994?w=600&h=600&fit=crop"),

        # Souslar
        (cat_ids["🥫 Souslar"], "Sous", 4000, "https://images.unsplash.com/photo-1585325701165-351af9ad665e?w=600&h=600&fit=crop")
    ]

    for cat_id, name, price, img in products:
        cursor.execute("INSERT INTO products (category_id, name, price, image) VALUES (?, ?, ?, ?)", (cat_id, name, price, img))

    conn.commit()
    conn.close()
    print("Database re-initialized with new menu!")

if __name__ == "__main__":
    reinit()
