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

class WarehouseStates(StatesGroup):
    warehouse_name = State()

class WarehouseOperationsStates(StatesGroup):
    warehouse_id = State()

class UserStates(StatesGroup):
    telegram_id = State()
    full_name = State()
    telegram_username = State()
    role = State()
    warehouse_id = State()

class EditUserStates(StatesGroup):
    id = State()
    edit_option = State()
    edit_data = State()

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

# Add user and linking warehouse
@admin_router.message(F.text=="Добавить пользователя", IsAdmin())
async def get_user_id(message: Message, state: FSMContext):
    await message.reply("Напишите telegram id пользователя. Чтобы узнать telegram id, попросите пользователя ввести команду /id", reply_markup=kb.cancel_admin_kb)
    await state.set_state(UserStates.telegram_id)

@admin_router.message(UserStates.telegram_id, IsAdmin())
async def get_user_full_name(message: Message, state: FSMContext):
    user_id = int(message.text)
    await state.update_data(telegram_id=user_id)
    await state.set_state(UserStates.full_name)

    await message.reply("Напишите Фамилия Имя", reply_markup=kb.cancel_admin_kb)

@admin_router.message(UserStates.full_name, IsAdmin())
async def get_username(message: Message, state: FSMContext):
    user_full_name = message.text
    await state.update_data(full_name=user_full_name)
    await state.set_state(UserStates.telegram_username)

    await message.reply("Напишите @username телеграм без @ (если нет - напишите 0)", reply_markup=kb.cancel_admin_kb)

@admin_router.message(UserStates.telegram_username, IsAdmin())
async def get_user_role(message: Message, state: FSMContext):
    username = message.text
    await state.update_data(telegram_username=username)
    await state.set_state(UserStates.role)

    await message.reply("Выберите роль пользователя", reply_markup=kb.roles_inline)


@admin_router.callback_query(UserStates.role, F.data == "admin", IsAdmin())
async def get_admin_warehouse(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Роль выбрана: Администратор")

    await state.update_data(role=callback.data)
    await state.set_state(UserStates.warehouse_id)

    markup = await kb.warehouses_main()

    await callback.message.answer(
        text="Выберите, к какому складу привязать администратора:",
        reply_markup=markup
    )


@admin_router.callback_query(UserStates.warehouse_id, IsAdmin())
async def get_admin_data(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    warehouse_id = int(callback.data)

    await callback.answer("Администратор привязан к складу")
    await state.update_data(warehouse_id=warehouse_id)
    await callback.message.answer("Администратор добавлен", reply_markup=kb.admin_kb)

    data = await state.get_data()
    await user_services.add_user(data["telegram_id"], data["full_name"], data["telegram_username"], data["role"],
                                 data["warehouse_id"])

    await state.clear()

@admin_router.callback_query(UserStates.role, F.data == "user", IsAdmin())
async def get_user_warehouse(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Роль выбрана: Пользователь")

    await state.update_data(role=callback.data)
    await state.set_state(UserStates.warehouse_id)

    markup = await kb.warehouses_main()

    await callback.message.answer(
        text="Выберите, к какому складу привязать пользователя:",
        reply_markup=markup
    )


@admin_router.callback_query(UserStates.warehouse_id, IsAdmin())
async def get_user_data(callback: CallbackQuery, state: FSMContext):
    warehouse_id = int(callback.data)
    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.answer("Пользователь привязан к складу")
    await state.update_data(warehouse_id=warehouse_id)
    await callback.message.answer("Пользователь добавлен", reply_markup=kb.admin_kb)

    data = await state.get_data()
    await user_services.add_user(data["telegram_id"], data["full_name"], data["telegram_username"], data["role"], data["warehouse_id"])

    await state.clear()

@admin_router.message(F.text=="Изменить пользователя", IsAdmin())
async def edit_user(message: Message, state: FSMContext):
    await state.set_state(EditUserStates.id)

    markup = await kb.users_main()
    await message.reply("Выберите пользователя для изменения", reply_markup=markup)

@admin_router.callback_query(EditUserStates.id, IsAdmin())
async def show_user_data_for_edit(callback: CallbackQuery, state: FSMContext):
    telegram_id = int(callback.data)
    user_data = await user_services.find_user(telegram_id)

    await callback.message.answer(f'Данные пользователя:\n'
                                  f'Имя: {user_data["full_name"]}\n'
                                  f'telegram_id: {user_data["telegram_id"]}\n'
                                  f'username: {user_data["username"]}\n'
                                  f'Роль: {user_data["role"]}\n'
                                  f'Склад: {user_data["warehouse_name"]}\n\n'
                                  f'✏️Для изменения данных выберите что именно хотите изменить', reply_markup=kb.edit_options_inline)

    await state.update_data(id=user_data["id"])
    await callback.message.delete()
    await state.set_state(EditUserStates.edit_option)


@admin_router.callback_query(EditUserStates.edit_option, IsAdmin())
async def get_edit_option(callback: CallbackQuery, state: FSMContext):
    option = callback.data
    await state.update_data(edit_option=option)
    await state.set_state(EditUserStates.edit_data)
    await callback.message.edit_reply_markup(reply_markup=None)

    markup_warehouse = await kb.warehouses_main()

    if option == "full_name":
        await callback.message.answer("Напишите Имя Фамилия")
    elif option == "telegram_id":
        await callback.message.answer("Напишите новый telegram_id")
    elif option == "username":
        await callback.message.answer("Напишите username без @")
    elif option == "role":
        await callback.message.answer("Выберите роль пользователя", reply_markup=kb.roles_inline)
    else:
        await callback.message.answer("Выберите новый склад для пользователя", reply_markup=markup_warehouse)


@admin_router.message(EditUserStates.edit_data, IsAdmin())
async def send_edit_text_data(message: Message, state: FSMContext):
    await state.update_data(edit_data=message.text)
    data = await state.get_data()
    option = data.get('edit_option')

    if option == "full_name":
        await user_services.edit_user_data(int(data.get('id')), data.get('edit_option'), data.get('edit_data'))
    elif option == "telegram_id":
        await user_services.edit_user_data(int(data.get('id')), data.get('edit_option'), data.get('edit_data'))
    elif option == "username":
        await user_services.edit_user_data(int(data.get('id')), data.get('edit_option'), data.get('edit_data'))

    await message.answer("Данные изменены успешно")
    await state.clear()

@admin_router.callback_query(EditUserStates.edit_data, IsAdmin())
async def send_edit_data(callback: CallbackQuery, state: FSMContext):
    await state.update_data(edit_data=callback.data)
    data = await state.get_data()
    option = data.get('edit_option')

    if option == "role":
        await user_services.edit_user_data(int(data.get('id')), data.get('edit_option'), data.get('edit_data'))
    elif option == "warehouse_id":
        await user_services.edit_user_data(int(data.get('id')), data.get('edit_option'), int(data.get('edit_data')))

    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer("Данные изменены успешно")
    await state.clear()

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
