from db.db import db

import asyncpg
import logging
from db.db import db

async def get_inventory(warehouse_id: int):
    inventory = await db.pool.fetch("""
        SELECT 
            warehouses.name AS warehouse,
            products.name AS product,
            inventory.quantity
        FROM inventory 
        LEFT JOIN warehouses 
            ON warehouses.id = inventory.warehouse_id
        LEFT JOIN products 
            ON products.id = inventory.product_id
        WHERE inventory.warehouse_id = $1
    """, warehouse_id
    )
    return inventory

async def get_products():
    products = await db.pool.fetch("""
        SELECT id, name FROM products ORDER BY id;
    """
    )
    return products

async def process_incoming_product(
    user_id: int,
    warehouse_id: int,
    product_id: int,
    quantity: int,
    comment: str
):
    try:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                # Обновляет/создает запись СТРОГО для комбинации (warehouse_id + product_id)
                await conn.execute("""
                    INSERT INTO inventory (warehouse_id, product_id, quantity)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (warehouse_id, product_id)
                    DO UPDATE SET quantity = inventory.quantity + $3;
                """, warehouse_id, product_id, quantity)

                # Записывает транзакцию с указанием конкретного склада
                await conn.execute("""
                    INSERT INTO transactions (user_id, warehouse_id, product_id, quantity, comment, operation_type)
                    VALUES ($1, $2, $3, $4, $5, 'incoming');
                """, user_id, warehouse_id, product_id, quantity, comment)

        return None
    except asyncpg.PostgresError as e:
        return str(e)

async def process_outgoing_product(
    user_id: int,
    warehouse_id: int,
    product_id: int,
    quantity: int,
    comment: str
):
    try:
        async with db.pool.acquire() as conn:
            async with conn.transaction():
                # Обновляет/создает запись СТРОГО для комбинации (warehouse_id + product_id)
                await conn.execute("""
                    UPDATE inventory
                        SET quantity = inventory.quantity - $3
                    WHERE warehouse_id = $1 AND product_id = $2 AND quantity >= $3;
                """, warehouse_id, product_id, quantity)

                # Записывает транзакцию с указанием конкретного склада
                await conn.execute("""
                    INSERT INTO transactions (user_id, warehouse_id, product_id, quantity, comment, operation_type)
                    VALUES ($1, $2, $3, $4, $5, 'outgoing');
                """, user_id, warehouse_id, product_id, quantity, comment)

        return None
    except asyncpg.PostgresError as e:
        return str(e)