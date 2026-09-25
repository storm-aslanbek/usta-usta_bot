import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers.admin import user_management
from handlers.user_handler import user_router
from handlers.admin.admin_handler import admin_router
from handlers.admin.user_management import router
from db.db import db

load_dotenv()
TG_TOKEN = os.getenv('TG_TOKEN')

dp = Dispatcher()
bot = Bot(token=TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

async def bot_main():
    dp.include_router(admin_router)
    dp.include_router(user_router)
    dp.include_router(user_management.router)
    await db.connect()

    try:
        await dp.start_polling(bot, skip_updates=True)
    finally:
        await db.disconnect()

if __name__ == '__main__':
    asyncio.run(bot_main())