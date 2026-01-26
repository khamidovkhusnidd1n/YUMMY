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
    
    for category, items in MENU.items():
        for item in items:
            image_path = item.get('image')
            if image_path and image_path not in processed_images:
                file_id = db.get_file_id(image_path)
                if not file_id:
                    print(f"Yuklanmoqda: {image_path}")
                    try:
                        photo = FSInputFile(image_path)
                        msg = await bot.send_photo(admin_id, photo, caption=f"Keshga yuklandi: {image_path}")
                        db.set_file_id(image_path, msg.photo[-1].file_id)
                        processed_images.add(image_path)
                    except Exception as e:
                        print(f"Xatolik {image_path} da: {e}")
                else:
                    print(f"Allaqachon keshda: {image_path}")
                    processed_images.add(image_path)
    
    print("Barcha rasmlar keshga yuklandi! [OK]")
    await bot.session.close()

if __name__ == "__main__":
    asyncio.run(warmup())
