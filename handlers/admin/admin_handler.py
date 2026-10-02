import time

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, BaseFilter, callback_data
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, WebAppInfo, CallbackQuery

from aiogram.fsm.state import State, StatesGroup

from services import warehouse_services, user_services, inventory_services

import keyboards as kb


class IsAdmin(BaseFilter):
    _admin_cache = []
    _last_update = 0
    CACHE_TTL = 3600

    async def __call__(self, message: Message) -> bool:
        current_time = time.time()

        if not IsAdmin._admin_cache or (current_time - IsAdmin._last_update) > IsAdmin.CACHE_TTL:
            IsAdmin._admin_cache = await user_services.get_admins()
            IsAdmin._last_update = current_time

        return message.from_user.id in IsAdmin._admin_cache


router = Router()

@router.message(Command("admin"), IsAdmin())
async def admin_message(message: Message):
    await message.answer("Ассалаумағалейкум админ!", reply_markup=kb.admin_kb)

@router.message(F.text=="Отмена", IsAdmin())
async def cancel_admin(message: Message, state: FSMContext):
    await message.answer("Асалаумағалейкум админ!", reply_markup=kb.admin_kb)
    await message.delete()
    await state.clear()

@router.message(F.text=="Склад", IsAdmin())
async def warehouse_main(message: Message, state: FSMContext):
    await message.answer("Выберите действие для склада", reply_markup=kb.admin_warehouse_operations_kb)

@router.message(F.text=="Пользователь", IsAdmin())
async def warehouse_main(message: Message, state: FSMContext):
    await message.answer("Выберите действие для пользователя", reply_markup=kb.admin_user_operations_kb)


@router.message(F.text=="Назад (как пользователь)")
async def back_message(message: Message):
    user = await user_services.find_user(message.from_user.id)

    if user:
        warehouse_text = user['warehouse_name'] if user['warehouse_name'] else "Все склады (Администратор)"
        await message.answer(
            f"Ассалаумағалейкум, {user['full_name']}!\n"
            f"📍 Вам доступен склад: {warehouse_text}",
            reply_markup=kb.user_kb
        )
    else:
        await message.answer(
            "Ассалаумағалейкум! Бот нужен для облегчения учета игрушек. Для пользования попросите Админстратора зарегестрировать вас. Удачи!",
            reply_markup=kb.user_kb)
