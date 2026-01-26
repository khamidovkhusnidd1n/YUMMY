import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
SUPER_ADMINS = [int(id.strip()) for id in os.getenv("SUPER_ADMINS", "").split(",") if id.strip()]
WORKERS = [int(id.strip()) for id in os.getenv("WORKERS", "").split(",") if id.strip()]
ALL_ADMINS = SUPER_ADMINS + WORKERS
