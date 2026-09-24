from db.db import db

# 1. Поиск пользователя по Telegram ID
async def get_user_by_telegram_id(telegram_id: int):
    """Возвращает данные пользователя или None"""
    return await db.pool.fetchrow("""
        SELECT * FROM users 
        WHERE telegram_id = $1;
    """, telegram_id)

async def add_user(telegram_id: int, full_name: str, role: str, warehouse_id: int):
    """Добавляет нового пользователя в базу"""
    await db.pool.execute("""
        INSERT INTO users (telegram_id, full_name, role, warehouse_id)
        VALUES ($1, $2, $3, $4);
    """, telegram_id, full_name, role)


