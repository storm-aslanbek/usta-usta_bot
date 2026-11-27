from db.db import db

async def get_warehouses():
    """Возвращает список всех складов из БД"""
    return await db.pool.fetch("""
        SELECT id, name FROM warehouses ORDER BY id;
    """)

async def get_warehouses_with_users():
    """Строка на каждого пользователя склада; у пустого склада full_name равен None"""
    return await db.pool.fetch("""
        SELECT
            warehouses.id,
            warehouses.name AS warehouse,
            users.full_name,
            users.role
        FROM warehouses
        LEFT JOIN users
            ON users.warehouse_id = warehouses.id AND users.is_active
        ORDER BY warehouses.name, warehouses.id, users.full_name;
    """)

async def get_warehouse_name(warehouse_id: int):
    return await db.pool.fetchval("""
        SELECT name FROM warehouses WHERE id = $1;
    """, warehouse_id)

async def add_warehouse(warehouse_name: str):
    await db.pool.execute("""
        INSERT INTO warehouses (name) VALUES ($1);
    """, warehouse_name)