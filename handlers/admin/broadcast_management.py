import asyncio
import html
from contextlib import suppress

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

import keyboards as kb
from handlers.admin.admin_handler import IsAdmin
from services import broadcast_services

router = Router()

ADMINS_ONLY_FOOTER = "🔒 Эту рассылку видят только администраторы"
ALBUM_WAIT_SECONDS = 1  # части альбома приходят отдельными сообщениями
question_lock = asyncio.Lock()  # чтобы быстрые сообщения не оставляли два вопроса


class BroadcastStates(StatesGroup):
    audience = State()
    content = State()


@router.message(F.text=="Рассылка", IsAdmin())
async def start_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BroadcastStates.audience)
    await message.answer("Кому отправить рассылку?", reply_markup=kb.broadcast_audience_inline)


@router.callback_query(BroadcastStates.audience, F.data.startswith("broadcast_to:"), IsAdmin())
async def choose_audience(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(audience=callback.data.split(":")[1], message_ids=[],
                            question_id=callback.message.message_id)
    await state.set_state(BroadcastStates.content)
    await callback.message.edit_text("Отправьте сообщение для рассылки",
                                     reply_markup=kb.broadcast_cancel_inline)


@router.message(BroadcastStates.content, IsAdmin())
async def receive_content(message: Message, state: FSMContext):
    """Запоминает сообщение или альбом. Новое сообщение заменяет прежнее"""
    data = await state.get_data()
    album_id = message.media_group_id

    if album_id is not None and album_id == data.get("album_id"):
        await state.update_data(message_ids=data["message_ids"] + [message.message_id])
        return

    await state.update_data(message_ids=[message.message_id], album_id=album_id)

    if album_id:
        await asyncio.sleep(ALBUM_WAIT_SECONDS)

    await ask_confirmation(message, state)


async def ask_confirmation(message: Message, state: FSMContext):
    """Заменяет прежний вопрос новым, чтобы он был под последним сообщением"""
    async with question_lock:
        # Пока ждали, рассылку могли отправить или отменить
        if await state.get_state() != BroadcastStates.content:
            return

        data = await state.get_data()
        with suppress(TelegramAPIError):
            await message.bot.delete_message(message.chat.id, data["question_id"])

        recipients = await broadcast_services.get_recipients(data["audience"])
        question = await message.answer(f"Вы уверены? Получателей: {len(recipients)}",
                                        reply_markup=kb.broadcast_confirm_inline)
        await state.update_data(question_id=question.message_id)


@router.callback_query(BroadcastStates.content, F.data == "broadcast_send", IsAdmin())
async def send_collected_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()

    # Двойное нажатие: первое уже забрало черновик
    if "message_ids" not in data:
        await callback.answer()
        return

    # Очищаем сразу, чтобы повторное нажатие не отправило рассылку дважды
    await state.clear()
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    recipients = await broadcast_services.get_recipients(data["audience"])
    footer = ADMINS_ONLY_FOOTER if data["audience"] == broadcast_services.AUDIENCE_ADMINS else None
    failed = await broadcast_services.send_broadcast(
        bot, recipients, callback.message.chat.id, data["message_ids"], footer)

    report = f"Доставлено {len(recipients) - len(failed)} из {len(recipients)}."
    if failed:
        names = ", ".join(html.escape(user["full_name"]) for user in failed)
        report += f"\nНе получили: {names}"

    await callback.message.answer(report, reply_markup=kb.admin_kb)


@router.callback_query(BroadcastStates.content, F.data == "broadcast_cancel", IsAdmin())
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    await callback.message.edit_text("Рассылка отменена")
    await callback.message.answer("Выберите действие", reply_markup=kb.admin_kb)
