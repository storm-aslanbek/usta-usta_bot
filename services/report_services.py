import logging

from db.db import db
from services import critical_stock_services
from .exceptions import GeneralDBError
from .history_services import TIMEZONE


# Начало периода: $1 - количество дней (0 - весь период), $2 - временная зона
PERIOD_CONDITION = """
    ($1::int = 0 OR transactions.created_at >=
        (date_trunc('day', now() AT TIME ZONE $2) - make_interval(days => $1::int - 1)) AT TIME ZONE $2)
"""


async def _fetch(query: str, *args):
    try:
        return await db.pool.fetch(query, *args)
    except Exception as e:
        logging.error(f"Database error during building report: {e}")
        raise GeneralDBError(internal_description=str(e))


async def get_stocks():
    """Остатки по всем складам, включая пустые (у них product и quantity равны None)"""
    return await _fetch("""
        SELECT
            warehouses.id AS warehouse_id,
            warehouses.name AS warehouse,
            products.name AS product,
            inventory.quantity
        FROM warehouses
        LEFT JOIN inventory ON inventory.warehouse_id = warehouses.id
        LEFT JOIN products ON products.id = inventory.product_id
        ORDER BY warehouses.name, products.id;
    """)


async def get_total_stocks():
    """Общее количество каждого товара по всем складам"""
    return await _fetch("""
        SELECT
            products.name AS product,
            COALESCE(SUM(inventory.quantity), 0)::bigint AS quantity
        FROM products
        LEFT JOIN inventory ON inventory.product_id = products.id
        GROUP BY products.id
        ORDER BY products.id;
    """)


async def get_critical_stocks():
    try:
        return await critical_stock_services.get_critical_stock()
    except Exception as e:
        logging.error(f"Database error during building report: {e}")
        raise GeneralDBError(internal_description=str(e))


async def add_warehouse_details(stocks):
    """Добавляет к остаткам пользователей склада и последнюю активность на нем"""
    users = await _fetch("""
        SELECT warehouse_id, string_agg(full_name, ', ' ORDER BY full_name) AS names
        FROM users
        WHERE is_active
        GROUP BY warehouse_id;
    """)
    activities = await _fetch("""
        SELECT DISTINCT ON (warehouses.id)
            warehouses.id AS warehouse_id,
            transactions.created_at AT TIME ZONE $1 AS created_at,
            transactions.operation_type,
            transactions.to_warehouse_id = warehouses.id AS is_incoming_transfer,
            users.full_name AS author
        FROM warehouses
        JOIN transactions
            ON transactions.warehouse_id = warehouses.id
            OR transactions.to_warehouse_id = warehouses.id
        JOIN users ON users.id = transactions.user_id
        ORDER BY warehouses.id, transactions.created_at DESC, transactions.id DESC;
    """, TIMEZONE)

    users_by_warehouse = {row["warehouse_id"]: row["names"] for row in users}
    activity_by_warehouse = {row["warehouse_id"]: row for row in activities}

    return [
        {
            **stock,
            "responsible": users_by_warehouse.get(stock["warehouse_id"]),
            "last_activity": activity_by_warehouse.get(stock["warehouse_id"]),
        }
        for stock in stocks
    ]


async def get_operations(days: int):
    """Операции всех складов за период, новые сверху"""
    return await _fetch(f"""
        SELECT
            transactions.operation_type,
            transactions.quantity,
            transactions.comment,
            transactions.created_at AT TIME ZONE $2 AS created_at,
            products.name AS product,
            users.full_name AS author,
            warehouses.name AS warehouse,
            recipient.name AS recipient_warehouse
        FROM transactions
        JOIN products ON products.id = transactions.product_id
        JOIN users ON users.id = transactions.user_id
        JOIN warehouses ON warehouses.id = transactions.warehouse_id
        LEFT JOIN warehouses AS recipient
            ON recipient.id = transactions.to_warehouse_id
        WHERE {PERIOD_CONDITION}
        ORDER BY transactions.created_at DESC, transactions.id DESC;
    """, days, TIMEZONE)
