from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.state import State, StatesGroup
from services import warehouse_services, inventory_services

import keyboards as kb

from handlers.admin.admin_handler import IsAdmin

router = Router()

@router.message(F.text=="Отчет", IsAdmin())
async def short_report(message: Message):
    await message.answer("Выберите какой формат отчета вы хотите", reply_markup=kb.reports_kb)



