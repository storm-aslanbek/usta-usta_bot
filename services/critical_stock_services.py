from db.db import db


CRITICAL_STOCK_THRESHOLD = 300


async def get_critical_stock():
    return await db.pool.fetch("""
        SELECT
            inventory.warehouse_id,
            warehouses.name AS warehouse,
            inventory.product_id,
            products.name AS product,
            inventory.quantity
        FROM inventory
        JOIN warehouses ON warehouses.id = inventory.warehouse_id
        JOIN products ON products.id = inventory.product_id
        WHERE inventory.quantity < $1
        ORDER BY warehouses.name, products.name;
    """, CRITICAL_STOCK_THRESHOLD)