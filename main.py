from datetime import datetime
import asyncio
import logging
import sys
import os
import json
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from config import BOT_TOKEN
from handlers import user_handlers, admin_handlers
from database import db

# Webhook configuration
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL") # Provided by Render automatically
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}" if WEBHOOK_HOST else None

# Server configuration
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

async def on_startup(bot: Bot) -> None:
    if WEBHOOK_URL:
        await bot.set_webhook(WEBHOOK_URL)
        print(f"Webhook set to: {WEBHOOK_URL}")

# --- WEB HANDLERS ---
async def web_index(request):
    """Serve the main index.html file"""
    return web.FileResponse('./index.html')

async def api_get_menu(request):
    """API endpoint to get dynamic menu data from database"""
    # Get all categories
    categories = db.get_all_categories()
    
    # Structure for the frontend: { "CategoryName": [ {item}, {item} ] }
    menu_data = {}
    
    # Categories table: id, name_uz, name_ru, name_en
    for cat in categories:
        cat_id = cat[0]
        cat_name = cat[1] # Using name_uz as the primary key for the menu dict
        
        items = db.get_products_by_category(cat_id)
        # Products table: id, category_id, name, price, image, is_available
        category_items = []
        for item in items:
            if item[5]: # is_available (index 5)
                category_items.append({
                    "id": item[0],
                    "n": item[2],       # name
                    "p": item[3],       # price
                    "i": item[4]        # image
                })
        
        if category_items:
            menu_data[cat_name] = category_items
            
    return web.json_response(menu_data)

async def api_validate_promo(request):
    """API endpoint to validate promo code from database"""
    try:
        data = await request.json()
        code = data.get('code', '').strip().upper()
        
        if not code:
            return web.json_response({"valid": False, "message": "Kod kiritilmadi"})
            
        promo = db.get_promo_code(code)
        if promo:
            # promo table: id, code, discount_percent, is_active, expiry_date
            return web.json_response({
                "valid": True,
                "discount": promo[2],
                "message": f"Tabriklaymiz! {promo[2]}% chegirma qabul qilindi."
            })
        else:
            return web.json_response({"valid": False, "message": "Promo-kod noto'g'ri yoki tugagan"})
    except Exception as e:
        return web.json_response({"valid": False, "message": f"Xatolik: {str(e)}"}, status=400)

def main():
    if not BOT_TOKEN:
        print("Iltimos, .env fayliga BOT_TOKEN ni kiriting!")
        return

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    # Auto-sync data if database is empty
    if not db.get_all_categories():
        print("Database categories table is empty. Initializing menu...")
        try:
            from init_menu import init_menu
            init_menu()
        except Exception as e:
            print(f"Init failed: {e}, trying JS sync...")
            try:
                from utils.sync_from_js import import_menu_from_js
                import_menu_from_js()
            except Exception as e2:
                print(f"JS sync also failed: {e2}")

    # Initialize admins from config
    from config import SUPER_ADMINS, WORKERS
    for admin_id in SUPER_ADMINS:
        # Always update super admin permissions to ensure they have all rights
        existing = db.get_admin(admin_id)
        if existing:
            db.update_admin_permissions(admin_id, 'manage_admins,menu,orders,promos,mailing,stats')
            db.update_admin_role(admin_id, 'super_admin')
        else:
            db.add_admin(admin_id, role='super_admin', permissions='manage_admins,menu,orders,promos,mailing,stats')
    for worker_id in WORKERS:
        if not db.get_admin(worker_id):
            db.add_admin(worker_id, role='admin', permissions='orders')
            
    # Always set up the web app (for both webhook and web interface)
    app = web.Application()
    
    # 1. Setup Request Handler for Bot Webhooks
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    setup_application(app, dp, bot=bot)

    # 2. Setup Web App Routes
    app.router.add_get('/', web_index)
    app.router.add_get('/api/menu', api_get_menu)
    app.router.add_post('/api/validate_promo', api_validate_promo)
    
    # 3. Setup Static Files
    # Serves the current directory for files like menu_data.js, utils.js
    app.router.add_static('/images', path='./images', name='images')
    
    # Specific files to prevent exposing .env or other source code
    async def serve_menu_data(request):
        return web.FileResponse('./menu_data.js')
    async def serve_utils(request):
        return web.FileResponse('./utils.js') if os.path.exists('./utils.js') else web.Response(text='')
    async def serve_simple_logic(request):
        return web.FileResponse('./simple_version_logic.js') if os.path.exists('./simple_version_logic.js') else web.Response(text='')
    
    app.router.add_get('/menu_data.js', serve_menu_data)
    app.router.add_get('/utils.js', serve_utils)
    app.router.add_get('/simple_version_logic.js', serve_simple_logic)

    # Register startup hooks
    if WEBHOOK_URL:
        dp.startup.register(on_startup)
    
    # Always run the scheduler
    async def on_startup_scheduler(bot: Bot):
        asyncio.create_task(daily_report_scheduler(bot))
    dp.startup.register(on_startup_scheduler)

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    print(f"Starting server on port {WEB_SERVER_PORT}...")
    
    # If running locally without a webhook URL, we can still run the web server
    # but might want polling for the bot.
    if not WEBHOOK_URL:
        print("No WEBHOOK_URL found. Bot will run in POLLING mode, but Web App is also available.")
        
        # We need to run polling in a separate task or just run app and use polling 
        # But aiohttp web.run_app is blocking.
        # Common pattern: use web.run_app and run polling in background OR
        # if dev mode, just run polling? 
        # Since user wants the Web App to work, we MUST run the web server.
        
        # For local dev with polling AND web server:
        async def run_polling_worker(app):
            await bot.delete_webhook(drop_pending_updates=True)
            asyncio.create_task(dp.start_polling(bot))
            yield
            
        app.cleanup_ctx.append(run_polling_worker)
        
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

async def daily_report_scheduler(bot: Bot):
    from config import SUPER_ADMINS
    from handlers.admin_handlers import generate_excel_report
    from aiogram import types
    import os
    
    while True:
        try:
            now = datetime.now()
            # Calculate time until 23:50
            target_time = now.replace(hour=23, minute=50, second=0, microsecond=0)
            if now >= target_time:
                from datetime import timedelta
                target_time += timedelta(days=1)
            
            wait_seconds = (target_time - now).total_seconds()
            print(f"Full daily report scheduled at 23:50. Waiting {wait_seconds} seconds.")
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


