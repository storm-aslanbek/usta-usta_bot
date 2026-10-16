import asyncio
import logging

from aiogram import Bot, Router

from services import critical_stock_services, user_services


router = Router()
CHECK_INTERVAL_SECONDS = 60
_notified_stocks = set()
_monitor_task = None


async def check_critical_stocks(bot: Bot):
    try:
        critical_stocks = await critical_stock_services.get_critical_stock()
        admin_ids = await user_services.get_admins()
    except Exception:
        logging.exception("Не удалось проверить критические остатки")
        return

    active_notifications = {
        (stock["warehouse_id"], stock["product_id"], admin_id)
        for stock in critical_stocks
        for admin_id in admin_ids
    }
    _notified_stocks.intersection_update(active_notifications)

    for stock in critical_stocks:
        for admin_id in admin_ids:
            notification_key = (
                stock["warehouse_id"],
                stock["product_id"],
                admin_id,
            )
            if notification_key in _notified_stocks:
                continue

            text = (
                "⚠️ Критический остаток товара!\n"
                f"Склад: {stock['warehouse']}\n"
                f"Товар: {stock['product']}\n"
                f"Остаток: {stock['quantity']} шт. "
                f"(порог: {critical_stock_services.CRITICAL_STOCK_THRESHOLD})"
            )
            try:
                await bot.send_message(chat_id=admin_id, text=text)
            except Exception:
                logging.exception(
                    "Не удалось отправить уведомление администратору %s",
                    admin_id,
                )
            else:
                _notified_stocks.add(notification_key)


async def _monitor_critical_stocks(bot: Bot):
    while True:
        await check_critical_stocks(bot)
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)


async def _start_monitoring(bot: Bot):
    global _monitor_task
    if _monitor_task is None or _monitor_task.done():
        _monitor_task = asyncio.create_task(_monitor_critical_stocks(bot))


async def _stop_monitoring(bot: Bot):
    if _monitor_task is not None:
        _monitor_task.cancel()
        try:
            await _monitor_task
        except asyncio.CancelledError:
            pass


router.startup.register(_start_monitoring)
router.shutdown.register(_stop_monitoring)