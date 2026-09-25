from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.warehouse_services import get_warehouses
from services.inventory_services import get_products
from services.user_services import get_users

main_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [
        KeyboardButton(text="В главное")
    ]
])

cancel_admin_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [
        KeyboardButton(text="Отмена")
    ]
])

cancel_user_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [
        KeyboardButton(text="❌Отмена")
    ]
])

user_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [
        KeyboardButton(text="Мои остатки"),
        KeyboardButton(text="Приход"),
        KeyboardButton(text="Расход"),
    ],
    [
        KeyboardButton(text="Перевод"),
        KeyboardButton(text="Инструкция"),
        KeyboardButton(text="История")
    ]
])

admin_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [
        KeyboardButton(text="Пользователь"),
        KeyboardButton(text="Склад"),
        KeyboardButton(text="Отчет")
    ],
    [
        KeyboardButton(text="Назад (как пользователь)")
    ]
])

admin_user_operations_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [
        KeyboardButton(text="Добавить пользователя"),
        KeyboardButton(text="Удалить пользователя")
    ],
    [
        KeyboardButton(text="Изменить пользователя"),
        KeyboardButton(text="Действия пользователя")
    ],
    [
        KeyboardButton(text="Отмена")
    ]
])

admin_warehouse_operations_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [
        KeyboardButton(text="Добавить склад"),
        KeyboardButton(text="Остатки по складу"),
    ],
    [
        KeyboardButton(text="Действия склада"),
    ],
    [
        KeyboardButton(text="Отмена")
    ]
])

roles_inline = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Администратор", callback_data="admin"),
        InlineKeyboardButton(text="Пользователь", callback_data="user")
    ]
])

async def warehouses_main():
    keyboard = InlineKeyboardBuilder()

    warehouses = await get_warehouses()

    for warehouse in warehouses:
        keyboard.add(
            InlineKeyboardButton(
                text=warehouse["name"],
                callback_data=str(warehouse['id'])
            )
        )

    return keyboard.adjust(2).as_markup()


async def products_main():
    keyboard = InlineKeyboardBuilder()

    products = await get_products()

    for product in products:
        keyboard.add(
            InlineKeyboardButton(
                text=product["name"],
                callback_data=str(product['id'])
            )
        )

    return keyboard.adjust(2).as_markup()

async def users_main():
    keyboard = InlineKeyboardBuilder()

    users = await get_users()

    for user in users:
        keyboard.add(
            InlineKeyboardButton(
                text=user["full_name"],
                callback_data=str(user['telegram_id'])
            )
        )

    return keyboard.adjust(2).as_markup()

edit_options_inline = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Имя", callback_data="full_name"),
        InlineKeyboardButton(text="telegram id", callback_data="telegram_id")
    ],
    [
        InlineKeyboardButton(text="username", callback_data="username"),
        InlineKeyboardButton(text="Роль", callback_data="role")
    ],
    [
        InlineKeyboardButton(text="Склад", callback_data="warehouse_id")
    ]
])