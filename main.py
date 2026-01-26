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

    # If RENDER_EXTERNAL_URL is set, use webhooks
    if WEBHOOK_HOST:
        dp.startup.register(on_startup)
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
            await dp.start_polling(bot)
        
        asyncio.run(run_polling())

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")

