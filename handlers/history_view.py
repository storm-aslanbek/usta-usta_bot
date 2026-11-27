import html

from aiogram.types import Message, BufferedInputFile

from services import history_services
from services.exceptions import ServiceError


PERIOD_TITLES = {
    history_services.ALL_TIME: "весь период",
    1: "сегодня",
    7: "7 дней",
    30: "30 дней",
}
COMMENT_MAX_LENGTH = 200
MESSAGE_MAX_LENGTH = 4000
MAX_MESSAGES_IN_CHAT = 3


def format_operation(operation) -> str:
    if operation["operation_type"] == "incoming":
        title, sign = "Приход", "+"
    elif operation["operation_type"] == "outgoing":
        title, sign = "Расход", "−"
    elif operation["is_incoming_transfer"]:
        title, sign = f'Перевод из «{html.escape(operation["sender_warehouse"])}»', "+"
    else:
        title, sign = f'Перевод в «{html.escape(operation["recipient_warehouse"])}»', "−"

    text = (
        f'{operation["created_at"]:%d.%m.%Y %H:%M} · {title}\n'
        f'{html.escape(operation["product"])}: {sign}{operation["quantity"]}\n'
        f'Кто: {html.escape(operation["author"])}'
    )

    comment = operation["comment"]
    if comment and comment != "0":
        text += f'\nКомментарий: {html.escape(comment[:COMMENT_MAX_LENGTH])}'

    return text


def split_into_messages(blocks: list[str]) -> list[str]:
    """Склеивает блоки в сообщения, не превышающие лимит Telegram"""
    messages = [blocks[0]]

    for block in blocks[1:]:
        if len(messages[-1]) + len(block) + 2 > MESSAGE_MAX_LENGTH:
            messages.append(block)
        else:
            messages[-1] += f"\n\n{block}"

    return messages


def build_text_file(blocks: list[str], filename: str) -> BufferedInputFile:
    # В файле HTML не разбирается, поэтому экранирование убираем
    text = html.unescape("\n\n".join(blocks))
    return BufferedInputFile(text.encode("utf-8-sig"), filename=filename)


async def send_long_text(message: Message, blocks: list[str], filename: str, reply_markup):
    """Отправляет текст сообщениями, а длинный - одним файлом с первым блоком в подписи"""
    texts = split_into_messages(blocks)

    if len(texts) > MAX_MESSAGES_IN_CHAT:
        await message.answer_document(build_text_file(blocks, filename), caption=blocks[0], reply_markup=reply_markup)
        return

    for text in texts:
        await message.answer(text, reply_markup=reply_markup)


async def send_history(message: Message, warehouse_id: int, days: int, warehouse_title: str, reply_markup):
    """Отправляет историю склада сообщениями, а длинную - одним файлом"""
    try:
        operations = await history_services.get_history(warehouse_id, days)
    except ServiceError as e:
        await message.answer(e.message_to_user, reply_markup=reply_markup)
        return

    if not operations:
        await message.answer("За этот период операций нет", reply_markup=reply_markup)
        return

    header = f"История {html.escape(warehouse_title)} за {PERIOD_TITLES[days]}"
    blocks = [header] + [format_operation(operation) for operation in operations]
    await send_long_text(message, blocks, "history.txt", reply_markup)
