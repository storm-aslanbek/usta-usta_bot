import time

from aiogram import Router, F
from aiogram.filters import CommandStart, Command, BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

import keyboards as kb
from services import user_services, inventory_services
from services.exceptions import ServiceError

router = Router()


class IsManager(BaseFilter):
    _manager_cache = []
    _last_update = 0
    CACHE_TTL = 3600

    async def __call__(self, message: Message) -> bool:
        current_time = time.time()

        if not IsManager._manager_cache or (current_time - IsManager._last_update) > IsManager.CACHE_TTL:
            users = await user_services.get_users()

            IsManager._manager_cache = [user['telegram_id'] for user in users]
            IsManager._last_update = current_time

        return message.from_user.id in IsManager._manager_cache


class ProductIncomingStates(StatesGroup):
    user_id = State()
    warehouse_id = State()
    product_id = State()
    toy_quantity = State()
    comment_text = State()

class ProductOutgoingStates(StatesGroup):
    user_id = State()
    warehouse_id = State()
    product_id = State()
    toy_quantity = State()
    comment_text = State()

class ProductTransferStates(StatesGroup):
    user_id = State()
    sender_warehouse_id = State()
    recipient_warehouse_id = State()
    product_id = State()
    toy_quantity = State()
    comment_text = State()

@router.message(CommandStart())
async def start_message(message: Message):
    user = await user_services.find_user(message.from_user.id)

    if user:
        warehouse_text = user['warehouse_name'] if user['warehouse_name'] else "Все склады (Администратор)"
        await message.answer(
            f"Ассалаумағалейкум, {user['full_name']}!\n"
            f"📍 Вам доступен склад: {warehouse_text}",
            reply_markup=kb.user_kb
        )
    else:
        await message.answer("Ассалаумағалейкум! Бот нужен для облегчения учета игрушек. Для пользования попросите Админстратора зарегестрировать вас. Удачи!", reply_markup=kb.user_kb)

@router.message(Command("id"))
async def get_user_data(message: Message):
    await message.answer(f'id: {message.from_user.id}\nИмя пользователя: {message.from_user.username}')

@router.message(F.text == "В главное")
async def move_to_main(message: Message):
    await message.answer(f'Выберите действие:', reply_markup=kb.user_kb)

@router.message(F.text=="❌Отмена", IsManager())
async def cancel_user(message: Message, state: FSMContext):
    user = await user_services.find_user(message.from_user.id)

    warehouse_text = user['warehouse_name'] if user['warehouse_name'] else "Все склады (Администратор)"
    await message.answer(
        f"Ассалаумағалейкум, {user['full_name']}!\n"
        f"📍 Вам доступен склад: {warehouse_text}",
        reply_markup=kb.user_kb)
    await state.clear()


# view inventory method
@router.message(F.text=="Мои остатки", IsManager())
async def inventory_handler(message: Message):
    data = await user_services.confirm_user(message.from_user.id)
    try:
        inventory = await inventory_services.get_inventory(data['warehouse_id'])

        filter_message = f'Остаток по складу "{inventory[0]["warehouse"]}"\n\n'

        for item in inventory:
            filter_message += f'{item["product"]}: {item["quantity"]}\n'

        await message.answer(filter_message, reply_markup=kb.main_kb)
    except ServiceError as e:
        await message.answer(e.message_to_user, reply_markup=kb.main_kb)


@router.message(F.text == "Инструкция")
async def send_instruction(message: Message):
    await message.answer(f'Бот предназначен для введение учета остатков на игрушек на складе. Всего имеется 2 категории игрушек: мелкие и большие. '
                         f'При новых поступлениях вы можете сделать приход или наоборот расход товара.\n'
                         f'-Мои остатки - для просмотра остатков на складе.\n'
                         f'-Приход - когда поступает партия игрушек\n'
                         f'-Расход - расход игрушек за день работы\n'
                         f'-Перевод - в случае если отправляете некое количество игрушек в другой город\n\n'
                         f'При вознекновении дополнительных вопросов или при форс мажоре связываться с Администратором +7 707 594 9376 Садыр',
                         reply_markup=kb.main_kb)



# incoming product
@router.message(F.text=="Приход", IsManager())
async def incoming_product(message: Message, state: FSMContext):
    await state.set_state(ProductIncomingStates.user_id)
    user_data = await user_services.confirm_user(message.from_user.id)
    await state.update_data(
        user_id=user_data["id"],
        warehouse_id=user_data["warehouse_id"]
    )

    await state.set_state(ProductIncomingStates.product_id)

    markup = await kb.products_main()
    await message.reply("Выберите категорию товара", reply_markup=markup)

@router.callback_query(ProductIncomingStates.product_id, IsManager())
async def get_product_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(product_id=int(callback.data))
    await state.set_state(ProductIncomingStates.toy_quantity)

    await callback.message.answer("Напишите количество игрушек (целое число без точек, запятых и пробелов)", reply_markup=kb.cancel_user_kb)
    await callback.message.delete()

@router.message(ProductIncomingStates.toy_quantity, IsManager())
async def get_product_quantity(message: Message, state: FSMContext):
    try:
        product_quantity = int(message.text)
        await state.update_data(toy_quantity=product_quantity)
        await state.set_state(ProductIncomingStates.comment_text)
        await message.answer("Напишите комментарий или напишите 0")
    except ValueError:
        await message.answer("Некорректное сообщение! Напишите количество целыми числами!", reply_markup=kb.cancel_user_kb)


@router.message(ProductIncomingStates.comment_text, IsManager())
async def send_incoming_data(message: Message, state: FSMContext):
    await state.update_data(comment_text=message.text)
    data = await state.get_data()

    try:
        await inventory_services.process_incoming_product(
            user_id=data["user_id"],
            warehouse_id=data["warehouse_id"],
            product_id=data["product_id"],
            quantity=data["toy_quantity"],
            comment=data["comment_text"]
        )
        await message.answer("✅ Приход товара успешно проведен!", reply_markup=kb.user_kb)
    except ServiceError as e:
        await message.answer(e.message_to_user, reply_markup=kb.user_kb)

    await state.clear()



# outgoing product
@router.message(F.text=="Расход", IsManager())
async def outgoing_product(message: Message, state: FSMContext):
    await state.set_state(ProductOutgoingStates.user_id)
    user_data = await user_services.confirm_user(message.from_user.id)
    await state.update_data(
        user_id=user_data["id"],
        warehouse_id=user_data["warehouse_id"]
    )

    await state.set_state(ProductOutgoingStates.product_id)

    markup = await kb.products_main()
    await message.reply("Выберите категорию товара", reply_markup=markup)

@router.callback_query(ProductOutgoingStates.product_id, IsManager())
async def outgoing_product_type(callback: CallbackQuery, state: FSMContext):
    await state.update_data(product_id=int(callback.data))
    await state.set_state(ProductOutgoingStates.toy_quantity)

    await callback.message.answer("Напишите количество игрушек (целое число без точек, запятых и пробелов)",
                                  reply_markup=kb.cancel_user_kb)
    await callback.message.delete()

@router.message(ProductOutgoingStates.toy_quantity, IsManager())
async def outgoing_product_quantity(message: Message, state: FSMContext):
    await state.update_data(toy_quantity=int(message.text))
    await state.set_state(ProductOutgoingStates.comment_text)
    await message.answer("Напишите комментарий или напишите 0")

@router.message(ProductOutgoingStates.comment_text, IsManager())
async def send_outgoing_data(message: Message, state: FSMContext):
    await state.update_data(comment_text=message.text)
    data = await state.get_data()

    try:
        await inventory_services.process_outgoing_product(
            user_id=data["user_id"],
            warehouse_id=data["warehouse_id"],
            product_id=data["product_id"],
            quantity=data["toy_quantity"],
            comment=data["comment_text"]
        )
        await message.answer("✅ Расход товара успешно проведен!", reply_markup=kb.user_kb)
    except ServiceError as e:
        await message.answer(e.message_to_user, reply_markup=kb.user_kb)

    await state.clear()


@router.message(F.text=="Перевод")
async def transfer_product(message: Message, state: FSMContext):
    markup = await kb.warehouses_main()
    await state.set_state(ProductTransferStates.user_id)
    user_data = await user_services.confirm_user(message.from_user.id)
    await state.update_data(
        user_id=user_data["id"],
        sender_warehouse_id=user_data["warehouse_id"]
    )
    await state.set_state(ProductTransferStates.recipient_warehouse_id)

    await message.reply("🛑Данная функция предназначена для перевода остатков на другой склад. Для списания или прихода расходов "
                         "используйте функции приход/расход", reply_markup=kb.cancel_user_kb)
    await message.answer("Выберите на какой склад произвести перевод остатков", reply_markup=markup)

@router.callback_query(ProductTransferStates.recipient_warehouse_id, IsManager())
async def get_recipient_warehouse(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)

    markup = await kb.products_main()
    recipient_data = int(callback.data)

    await state.update_data(recipient_warehouse_id=recipient_data)
    await state.set_state(ProductTransferStates.product_id)

    await callback.message.answer("Выберите тип игрушек для перевода", reply_markup=markup)

@router.callback_query(ProductTransferStates.product_id, IsManager())
async def get_product_type_for_transfer(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)

    product_data = int(callback.data)

    await state.update_data(product_id=product_data)
    await state.set_state(ProductTransferStates.toy_quantity)

    await callback.message.answer("Напишите количество игрушек (целое число без точек, запятых и пробелов)", reply_markup=kb.cancel_user_kb)

@router.message(ProductTransferStates.toy_quantity, IsManager())
async def get_toy_quantity(message: Message, state: FSMContext):
    toy_quantity = int(message.text)

    await state.update_data(toy_quantity=toy_quantity)
    await state.set_state(ProductTransferStates.comment_text)

    await message.answer("Напишите комментарии или напишите 0 (Можете написать стоимость такси/логистики", reply_markup=kb.cancel_user_kb)

@router.message(ProductTransferStates.comment_text, IsManager())
async def get_data_to_transfer(message: Message, state: FSMContext):
    await state.update_data(comment_text=message.text)
    data = await state.get_data()

    try:
        await inventory_services.process_trtansfer_product(
            user_id=data["user_id"],
            sender_warehouse_id=data["sender_warehouse_id"],
            recipient_warehouse_id=data["recipient_warehouse_id"],
            product_id=data["product_id"],
            product_quantity=data["toy_quantity"],
            comment=data["comment_text"]
        )
        await message.answer("✅ Перевод товара успешно проведен!", reply_markup=kb.user_kb)
    except ServiceError as e:
        await message.answer(e.message_to_user, reply_markup=kb.user_kb)

    await state.clear()


@router.message(F.text)
async def echo_message(message: Message):
    await message.answer("Нет прав или неправильная команда")