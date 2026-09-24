from db.db import db

async def get_warehouses():
    """Возвращает список всех складов из БД"""
    return await db.pool.fetch("""
        SELECT id, name FROM warehouses ORDER BY id;
    """)

async def add_warehouse(warehouse_name: str):
    await db.pool.execute("""
        INSERT INTO warehouses (name) VALUES ($1);
    """, warehouse_name)