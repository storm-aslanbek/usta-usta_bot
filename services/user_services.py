import asyncpg

from db.db import db
from .exceptions import NotFoundError, UserAlreadyExistsError, ValidationError

async def add_user(telegram_id: int, full_name: str, username, role: str, warehouse_id: int):
    """Добавляет нового пользователя или восстанавливает удаленного"""
    status = await db.pool.execute("""
        INSERT INTO users (telegram_id, full_name, username, role, warehouse_id)
        VALUES ($1, $2, $3, $4, $5)
        ON CONFLICT (telegram_id) DO UPDATE
            SET full_name = $2, username = $3, role = $4, warehouse_id = $5, is_active = TRUE
            WHERE NOT users.is_active;
    """, telegram_id, full_name, username, role, warehouse_id)

    if status == 'INSERT 0 0':
        raise UserAlreadyExistsError()

async def deactivate_user(telegram_id: int, admin_telegram_id: int):
    """Отключает пользователя, сохраняя его операции в истории"""
    if telegram_id == admin_telegram_id:
        raise ValidationError("Нельзя удалить самого себя.")

    status = await db.pool.execute("""
        UPDATE users
        SET is_active = FALSE
        WHERE telegram_id = $1 AND is_active;
    """, telegram_id)

    if status == 'UPDATE 0':
        raise NotFoundError("Пользователь")

async def find_user(telegram_id: int):
    return await db.pool.fetchrow("""
        SELECT 
            users.telegram_id,
            users.full_name, 
            users.username, 
            users.role, 
            warehouses.name AS warehouse_name,
            users.id
        FROM users
        LEFT JOIN warehouses ON users.warehouse_id = warehouses.id
        WHERE users.telegram_id = $1 AND users.is_active;
    """, telegram_id)

async def get_users():
    return await db.pool.fetch("""
        SELECT
            telegram_id,
            full_name
        FROM users
        WHERE is_active;
    """)

async def get_users_with_warehouses():
    return await db.pool.fetch("""
        SELECT
            users.full_name,
            users.username,
            users.role,
            warehouses.name AS warehouse_name
        FROM users
        LEFT JOIN warehouses ON users.warehouse_id = warehouses.id
        WHERE users.is_active
        ORDER BY users.full_name;
    """)

async def confirm_user(telegram_id: int):
    return await db.pool.fetchrow("""
        SELECT users.id,
             warehouses.id AS warehouse_id
        FROM users
        LEFT JOIN warehouses ON users.warehouse_id = warehouses.id
        WHERE users.telegram_id = $1 AND users.is_active;
    """, telegram_id)

async def get_admins():
    admins =  await db.pool.fetch("""
        SELECT telegram_id
            FROM users
            WHERE role = 'admin' AND is_active;
    """)

    admin_list = [admin['telegram_id'] for admin in admins]
    return admin_list


async def edit_user_data(id: int, edit_option: str, edit_data):
    allowed_columns = ["full_name", "telegram_id", "username", "role", "warehouse_id"]

    column_name = edit_option
    if column_name not in allowed_columns:
        raise ValueError(f"Недопустимое имя колонки: {column_name}")

    query = f"""
            UPDATE users
            SET {column_name} = $1
            WHERE id = $2;
        """

    try:
        return await db.pool.execute(query, edit_data, id)
    except asyncpg.UniqueViolationError:
        raise UserAlreadyExistsError()