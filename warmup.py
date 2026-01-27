import asyncio
from aiogram import Bot
from config import BOT_TOKEN, SUPER_ADMINS
from menu import MENU
from database import db
from aiogram.types import FSInputFile

async def warmup():
    if not SUPER_ADMINS:
        print("SUPER_ADMINS bo'sh. Iltimos, config.py ga o'z IDingizni kiriting.")
        return
        
    bot = Bot(token=BOT_TOKEN)
    admin_id = SUPER_ADMINS[0]
    
    print("Rasmlarni keshga yuklash boshlandi...")
    
    processed_images = set()
    
    # 1. Warmup from static MENU (menu.py)
    for category, items in MENU.items():
        for item in items:
            image_path = item.get('image')
            if image_path and image_path not in processed_images:
                await cache_image(bot, admin_id, image_path, processed_images)

    # 2. Warmup from Database (products table)
    db_products = db.cursor.execute("SELECT image FROM products").fetchall()
    for (image_path,) in db_products:
        if image_path and image_path not in processed_images:
            await cache_image(bot, admin_id, image_path, processed_images)
    
    print("Barcha rasmlar keshga yuklandi! [OK]")
    await bot.session.close()

async def cache_image(bot, admin_id, image_path, processed_set):
    file_id = db.get_file_id(image_path)
    if not file_id:
        print(f"Yuklanmoqda: {image_path}")
        try:
            photo = FSInputFile(image_path)
            msg = await bot.send_photo(admin_id, photo, caption=f"Keshga yuklandi: {image_path}")
            db.set_file_id(image_path, msg.photo[-1].file_id)
            processed_set.add(image_path)
        except Exception as e:
            print(f"Xatolik {image_path} da: {e}")
    else:
        print(f"Allaqachon keshda: {image_path}")
        processed_set.add(image_path)

if __name__ == "__main__":
    asyncio.run(warmup())
