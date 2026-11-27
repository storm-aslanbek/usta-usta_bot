from db.db import db

async def get_warehouses():
    """Возвращает список всех складов из БД"""
    return await db.pool.fetch("""
        SELECT id, name FROM warehouses ORDER BY id;
    """)

async def get_warehouse_name(warehouse_id: int):
    return await db.pool.fetchval("""
        SELECT name FROM warehouses WHERE id = $1;
    """, warehouse_id)

async def add_warehouse(warehouse_name: str):
    await db.pool.execute("""
        INSERT INTO warehouses (name) VALUES ($1);
    """, warehouse_name)