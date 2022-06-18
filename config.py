import os
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import logging
from dotenv import load_dotenv

load_dotenv("keys.env")

image_folder_path = "code_pictures"
DATABASE_CONFIG = {
    "connections": {
        # Using a DB_URL string
        "default": os.environ.get("DATABASE_URL"),
    },
    "apps": {
        "bot": {
            "models": ["models", "aerich.models"],
            # If no default_connection specified, defaults to 'default'
            "default_connection": "default",
        }
    },
    "use_tz": True,
    "timezone": "UTC",
}

bot = Bot(token=os.environ.get("TOKEN"), parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)
list_limiter = 10
