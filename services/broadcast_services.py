import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from services import user_services


AUDIENCE_ALL = "all"
AUDIENCE_ADMINS = "admins"

COPY_MESSAGES_LIMIT = 100  # ограничение Telegram на один вызов copy_messages


async def get_recipients(audience: str):
    """Активные пользователи, которым предназначена рассылка"""
    users = await user_services.get_users()

    if audience == AUDIENCE_ALL:
        return users

    admin_ids = await user_services.get_admins()
    return [user for user in users if user["telegram_id"] in admin_ids]


async def send_broadcast(bot: Bot, recipients, from_chat_id: int, message_ids: list[int], footer: str = None):
    """Копирует сообщения получателям. Возвращает тех, кому доставить не удалось"""
    failed = []
    ordered_ids = sorted(message_ids)

    for recipient in recipients:
        try:
            await _send_to_chat(bot, recipient["telegram_id"], from_chat_id, ordered_ids, footer)
        except TelegramAPIError as e:
            logging.warning(f"Broadcast was not delivered to {recipient['telegram_id']}: {e}")
            failed.append(recipient)

    return failed


async def _send_to_chat(bot: Bot, chat_id: int, from_chat_id: int, message_ids: list[int], footer: str):
    for start in range(0, len(message_ids), COPY_MESSAGES_LIMIT):
        await bot.copy_messages(
            chat_id=chat_id,
            from_chat_id=from_chat_id,
            message_ids=message_ids[start:start + COPY_MESSAGES_LIMIT],
        )

    if footer:
        await bot.send_message(chat_id=chat_id, text=footer)
