from aiogram import Router, F
from aiogram.filters import CommandStart, Command, BaseFilter, callback_data
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, WebAppInfo, CallbackQuery

from aiogram.fsm.state import State, StatesGroup

from services import warehouse_services, user_services, inventory_services

import keyboards as kb


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message) -> bool:
        admin_id_list = await user_services.get_admins()

        return message.from_user.id in admin_id_list


admin_router = Router()

@admin_router.message(Command("admin"), IsAdmin())
async def admin_message(message: Message):
    await message.answer("Ассалаумағалейкум админ!", reply_markup=kb.admin_kb)

@admin_router.message(F.text=="Отмена", IsAdmin())
async def cancel_admin(message: Message, state: FSMContext):
    await message.answer("Асалаумағалейкум админ!", reply_markup=kb.admin_kb)
    await message.delete()
    await state.clear()

@admin_router.message(F.text=="Склад", IsAdmin())
async def warehouse_main(message: Message, state: FSMContext):
    await message.answer("Выберите действие для склада", reply_markup=kb.admin_warehouse_operations_kb)

@admin_router.message(F.text=="Пользователь", IsAdmin())
async def warehouse_main(message: Message, state: FSMContext):
    await message.answer("Выберите действие для пользователя", reply_markup=kb.admin_user_operations_kb)


@admin_router.message(F.text=="Назад (как пользователь)")
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
