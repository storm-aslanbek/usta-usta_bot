import asyncio
import os

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from handlers import user_handler
from handlers.admin import admin_handler, user_management, warehouse_management
from db.db import db

load_dotenv()
TG_TOKEN = os.getenv('TG_TOKEN')

dp = Dispatcher()
bot = Bot(token=TG_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

async def bot_main():
    dp.include_router(admin_handler.router)
    dp.include_router(user_management.router)
    dp.include_router(warehouse_management.router)
    dp.include_router(user_handler.router)
    await db.connect()

    try:
        await dp.start_polling(bot)
    finally:
        await db.disconnect()

if __name__ == '__main__':
    asyncio.run(bot_main())