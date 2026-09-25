from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from aiogram.fsm.state import State, StatesGroup
from services import warehouse_services, inventory_services

import keyboards as kb

from admin_handler import admin_router
from admin_handler import IsAdmin

class WarehouseStates(StatesGroup):
    warehouse_name = State()

class WarehouseOperationsStates(StatesGroup):
    warehouse_id = State()

# Add warehouse
@admin_router.message(F.text=="Добавить склад", IsAdmin())
async def add_warehouse(message: Message, state: FSMContext):
    await state.set_state(WarehouseStates.warehouse_name)
    await message.reply("Напишите название склада", reply_markup=kb.cancel_admin_kb)

@admin_router.message(WarehouseStates.warehouse_name, IsAdmin())
async def reply_warehouse_message(message: Message, state: FSMContext):
    warehouse_name = message.text
    await state.update_data(warehouse_name=warehouse_name)
    data = await state.get_data()

    await warehouse_services.add_warehouse(data["warehouse_name"])
    await message.answer(f'Склад "{warehouse_name}" успешно добавлен.', reply_markup=kb.admin_kb)

    await state.clear()


@admin_router.message(F.text=="Остатки по складу", IsAdmin())
async def get_warehouse_inventory(message: Message, state: FSMContext):
    markup = await kb.warehouses_main()
    await message.answer("Выберите склад", reply_markup=markup)

    await state.set_state(WarehouseOperationsStates.warehouse_id)

@admin_router.callback_query(WarehouseOperationsStates.warehouse_id, IsAdmin())
async def select_warehouse(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    warehouse_id = int(callback.data)
    inventory = await inventory_services.get_inventory(warehouse_id)
    filter_message = f'Остаток по складу "{inventory[0]["warehouse"]}"\n\n'

    for item in inventory:
        filter_message += f'{item["product"]}: {item["quantity"]}\n'

    await callback.message.answer(filter_message, reply_markup=kb.admin_kb)
