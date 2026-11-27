import html

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

import keyboards as kb
from handlers.admin.admin_handler import IsAdmin
from services import broadcast_services

router = Router()

ADMINS_ONLY_FOOTER = "🔒 Эту рассылку видят только администраторы"


class BroadcastStates(StatesGroup):
    audience = State()
    messages = State()
    confirmation = State()


@router.message(F.text=="Рассылка", IsAdmin())
async def start_broadcast(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(BroadcastStates.audience)
    await message.answer("Кому отправить рассылку?", reply_markup=kb.broadcast_audience_inline)


@router.callback_query(BroadcastStates.audience, F.data.startswith("broadcast_to:"), IsAdmin())
async def choose_audience(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    await state.update_data(audience=callback.data.split(":")[1], message_ids=[])
    await state.set_state(BroadcastStates.messages)

    await callback.message.answer(
        "Отправьте одно или несколько сообщений (текст, фото, видео, файлы), "
        "затем нажмите «Отправить рассылку»",
        reply_markup=kb.broadcast_compose_kb)


# Должен стоять выше collect_message, иначе кнопка попадет в рассылку
@router.message(BroadcastStates.messages, F.text=="Отправить рассылку", IsAdmin())
async def ask_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()

    if not data["message_ids"]:
        await message.answer("Сначала отправьте сообщение для рассылки")
        return

    recipients = await broadcast_services.get_recipients(data["audience"])
    await state.set_state(BroadcastStates.confirmation)
    await message.answer(f"Получателей: {len(recipients)}. Отправить?",
                         reply_markup=kb.broadcast_confirm_inline)


@router.message(BroadcastStates.messages, IsAdmin())
async def collect_message(message: Message, state: FSMContext):
    data = await state.get_data()
    await state.update_data(message_ids=data["message_ids"] + [message.message_id])


@router.callback_query(BroadcastStates.confirmation, F.data == "broadcast_yes", IsAdmin())
async def send_confirmed_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)

    data = await state.get_data()
    # Очищаем сразу, чтобы повторное нажатие не отправило рассылку дважды
    await state.clear()

    recipients = await broadcast_services.get_recipients(data["audience"])
    footer = ADMINS_ONLY_FOOTER if data["audience"] == broadcast_services.AUDIENCE_ADMINS else None
    failed = await broadcast_services.send_broadcast(
        bot, recipients, callback.message.chat.id, data["message_ids"], footer)

    report = f"Доставлено {len(recipients) - len(failed)} из {len(recipients)}."
    if failed:
        names = ", ".join(html.escape(user["full_name"]) for user in failed)
        report += f"\nНе получили: {names}"

    await callback.message.answer(report, reply_markup=kb.admin_kb)


@router.callback_query(BroadcastStates.confirmation, F.data == "broadcast_no", IsAdmin())
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text("Рассылка отменена")
    await callback.message.answer("Выберите действие", reply_markup=kb.admin_kb)
    await state.clear()
