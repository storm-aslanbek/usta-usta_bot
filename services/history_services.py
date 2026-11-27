import logging

from db.db import db
from .exceptions import GeneralDBError


TIMEZONE = "Asia/Almaty"
ALL_TIME = 0


async def get_history(warehouse_id: int, days: int):
    """Операции склада за последние дни (включая сегодня) или ALL_TIME, новые сверху"""
    try:
        return await db.pool.fetch("""
            SELECT
                transactions.operation_type,
                transactions.quantity,
                transactions.comment,
                transactions.created_at AT TIME ZONE $3 AS created_at,
                transactions.to_warehouse_id = $1 AS is_incoming_transfer,
                products.name AS product,
                users.full_name AS author,
                sender.name AS sender_warehouse,
                recipient.name AS recipient_warehouse
            FROM transactions
            JOIN products ON products.id = transactions.product_id
            JOIN users ON users.id = transactions.user_id
            LEFT JOIN warehouses AS sender
                ON sender.id = transactions.from_warehouse_id
            LEFT JOIN warehouses AS recipient
                ON recipient.id = transactions.to_warehouse_id
            WHERE (transactions.warehouse_id = $1 OR transactions.to_warehouse_id = $1)
                AND ($2::int = 0 OR transactions.created_at >=
                    (date_trunc('day', now() AT TIME ZONE $3) - make_interval(days => $2::int - 1)) AT TIME ZONE $3)
            ORDER BY transactions.created_at DESC, transactions.id DESC;
        """, warehouse_id, days, TIMEZONE)
    except Exception as e:
        logging.error(f"Database error during getting history: {e}")
        raise GeneralDBError(internal_description=str(e))
