from db.db import db

async def add_user(telegram_id: int, full_name: str, username, role: str, warehouse_id: int):
    """Добавляет нового пользователя в базу"""
    await db.pool.execute("""
        INSERT INTO users (telegram_id, full_name, username, role, warehouse_id)
        VALUES ($1, $2, $3, $4, $5);
    """, telegram_id, full_name, username, role, warehouse_id)

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
        WHERE users.telegram_id = $1;
    """, telegram_id)

async def get_users():
    return await db.pool.fetch("""
        SELECT
            telegram_id,
            full_name
        FROM users;
    """)

async def confirm_user(telegram_id: int):
    return await db.pool.fetchrow("""
        SELECT users.id,
             warehouses.id AS warehouse_id
        FROM users
        LEFT JOIN warehouses ON users.warehouse_id = warehouses.id
        WHERE users.telegram_id = $1;
    """, telegram_id)

async def get_admins():
    admins =  await db.pool.fetch("""
        SELECT telegram_id
            FROM users
            WHERE role = 'admin';
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

    return await db.pool.execute(query, edit_data, id)