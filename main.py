from datetime import datetime
import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import BOT_TOKEN
from handlers import user_handlers, admin_handlers

# Webhook configuration
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL") # Provided by Render automatically
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Server configuration
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

async def on_startup(bot: Bot) -> None:
    await bot.set_webhook(WEBHOOK_URL)
    print(f"Webhook set to: {WEBHOOK_URL}")

def main():
    if not BOT_TOKEN:
        print("Iltimos, .env fayliga BOT_TOKEN ni kiriting!")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    # Initialize admins from config
    from config import SUPER_ADMINS, WORKERS
    from database import db
    for admin_id in SUPER_ADMINS:
        if not db.get_admin(admin_id):
            db.add_admin(admin_id, role='super_admin', permissions='manage_admins,menu,orders,promos,mailing,stats')
    for worker_id in WORKERS:
        if not db.get_admin(worker_id):
            db.add_admin(worker_id, role='admin', permissions='orders')

    # If RENDER_EXTERNAL_URL is set, use webhooks
    if WEBHOOK_HOST:
        dp.startup.register(on_startup)
        async def on_startup_scheduler(bot: Bot):
            asyncio.create_task(daily_report_scheduler(bot))
        dp.startup.register(on_startup_scheduler)

        app = web.Application()
        webhook_requests_handler = SimpleRequestHandler(
            dispatcher=dp,
            bot=bot,
        )
        webhook_requests_handler.register(app, path=WEBHOOK_PATH)
        setup_application(app, dp, bot=bot)
        
        logging.basicConfig(level=logging.INFO, stream=sys.stdout)
        print(f"Starting server on port {WEB_SERVER_PORT}...")
        web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)
    else:
        # Otherwise use local polling
        async def run_polling():
            logging.basicConfig(level=logging.INFO, stream=sys.stdout)
            print("Starting polling mode (Local)...")
            asyncio.create_task(daily_report_scheduler(bot))
            await dp.start_polling(bot)
        
        asyncio.run(run_polling())

async def daily_report_scheduler(bot: Bot):
    from config import SUPER_ADMINS
    from handlers.admin_handlers import generate_excel_report
    from aiogram import types
    import os
    
    while True:
        try:
            now = datetime.now()
            # Calculate time until midnight (00:00)
            target_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
            if now >= target_time:
                from datetime import timedelta
                target_time += timedelta(days=1)
            
            wait_seconds = (target_time - now).total_seconds()
            print(f"Daily report scheduled in {wait_seconds} seconds.")
            await asyncio.sleep(wait_seconds)
            
            # Generate and send report
            file_path = await generate_excel_report()
            for admin_id in SUPER_ADMINS:
                try:
                    await bot.send_document(
                        admin_id, 
                        types.FSInputFile(file_path), 
                        caption=f"📝 Kunlik hisobot: {datetime.now().strftime('%Y-%m-%d')}"
                    )
                except Exception as e:
                    print(f"Error sending daily report to {admin_id}: {e}")
            
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Wait a bit to avoid double send in the same second
            await asyncio.sleep(60)
        except Exception as e:
            print(f"Error in daily_report_scheduler: {e}")
            await asyncio.sleep(3600) # Wait an hour before retrying if error

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")


