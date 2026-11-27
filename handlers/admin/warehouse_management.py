from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.state import State, StatesGroup
from services import warehouse_services, inventory_services

import keyboards as kb

from handlers.admin.admin_handler import IsAdmin
from handlers.history_view import send_history

class WarehouseStates(StatesGroup):
    warehouse_name = State()

class WarehouseOperationsStates(StatesGroup):
    warehouse_id = State()

class WarehouseHistoryStates(StatesGroup):
    warehouse_id = State()

router = Router()

# Add warehouse
@router.message(F.text=="Добавить склад", IsAdmin())
async def add_warehouse(message: Message, state: FSMContext):
    await state.set_state(WarehouseStates.warehouse_name)
    await message.reply("Напишите название склада", reply_markup=kb.cancel_admin_kb)

@router.message(WarehouseStates.warehouse_name, IsAdmin())
async def reply_warehouse_message(message: Message, state: FSMContext):
    warehouse_name = message.text
    await state.update_data(warehouse_name=warehouse_name)
    data = await state.get_data()

    await warehouse_services.add_warehouse(data["warehouse_name"])
    await message.answer(f'Склад "{warehouse_name}" успешно добавлен.', reply_markup=kb.admin_kb)

    await state.clear()


@router.message(F.text=="Остатки по складу", IsAdmin())
async def get_warehouse_inventory(message: Message, state: FSMContext):
    markup = await kb.warehouses_main()
    await message.answer("Выберите склад", reply_markup=markup)

    await state.set_state(WarehouseOperationsStates.warehouse_id)

@router.callback_query(WarehouseOperationsStates.warehouse_id, F.data.isdigit(), IsAdmin())
async def select_warehouse(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    warehouse_id = int(callback.data)
    inventory = await inventory_services.get_inventory(warehouse_id)

    if not inventory:
        await callback.message.answer("На складе пока нет товаров", reply_markup=kb.admin_kb)
        return

    filter_message = f'Остаток по складу "{inventory[0]["warehouse"]}"\n\n'

    for item in inventory:
        filter_message += f'{item["product"]}: {item["quantity"]}\n'

    await callback.message.answer(filter_message, reply_markup=kb.admin_kb)

# Warehouse history
@router.message(F.text=="Действия склада", IsAdmin())
async def choose_history_warehouse(message: Message, state: FSMContext):
    await state.set_state(WarehouseHistoryStates.warehouse_id)
    markup = await kb.warehouses_main()
    await message.answer("Выберите склад", reply_markup=markup)

@router.callback_query(WarehouseHistoryStates.warehouse_id, F.data.isdigit(), IsAdmin())
async def choose_history_period(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer()
    markup = kb.history_periods(f"warehouse_history:{int(callback.data)}")
    await callback.message.edit_text("За какой период?", reply_markup=markup)

@router.callback_query(F.data.startswith("warehouse_history:"), IsAdmin())
async def show_warehouse_history(callback: CallbackQuery):
    await callback.answer()
    _, warehouse_id, days = callback.data.split(":")
    warehouse_name = await warehouse_services.get_warehouse_name(int(warehouse_id))

    await send_history(callback.message, int(warehouse_id), int(days), f"склада «{warehouse_name}»", kb.admin_kb)
