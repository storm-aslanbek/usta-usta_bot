import asyncpg
import logging
import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URI = os.getenv("POSTGRES_URI")
# Параметры подключения к вашей PostgreSQL
DB_CONFIG = {
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": 5432,
    "database": "usta_usta"
}

class Database:
    def __init__(self):
        self.pool: asyncpg.Pool = None

    async def connect(self):
        """Создаем пул подключений при старте бота"""
        self.pool = await asyncpg.create_pool(dsn=POSTGRES_URI)
        logging.info("Пул подключений к PostgreSQL успешно создан!")

    async def disconnect(self):
        """Закрываем пул при остановке бота"""
        if self.pool:
            await self.pool.close()
            logging.info("Подключение к PostgreSQL закрыто.")

# Создаем единый экземпляр класса для работы в проекте
db = Database()