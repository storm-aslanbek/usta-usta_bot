from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

import keyboards as kb
from handlers import report_excel, report_view
from handlers.admin.admin_handler import IsAdmin
from handlers.history_view import send_long_text
from services import report_services
from services.exceptions import ServiceError

router = Router()

WEEK_DAYS = 7
REPORT_BUTTONS = {
    "Остатки": "stocks",
    "Операции за неделю": "operations",
    "Критические остатки": "critical",
}


@router.message(F.text=="Отчет", IsAdmin())
async def show_reports_menu(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите отчет", reply_markup=kb.reports_kb)


@router.message(F.text.in_(REPORT_BUTTONS), IsAdmin())
async def choose_report_format(message: Message, state: FSMContext):
    await state.clear()
    markup = kb.report_formats(REPORT_BUTTONS[message.text])
    await message.answer(f"{message.text}: в каком виде?", reply_markup=markup)


async def send_stocks(message: Message, file_format: str):
    stocks = await report_services.get_stocks()

    if not stocks:
        await message.answer("Складов пока нет", reply_markup=kb.reports_kb)
        return

    totals = await report_services.get_total_stocks()

    if file_format == "excel":
        rows = await report_services.add_warehouse_details(stocks)
        await message.answer_document(report_excel.build_stocks_file(rows, "stocks.xlsx", totals))
    else:
        blocks = ["Остатки по всем складам"] + report_view.format_stocks(stocks)
        blocks.append(report_view.format_total_stocks(totals))
        await send_long_text(message, blocks, "stocks.txt", kb.reports_kb)


async def send_critical_stocks(message: Message, file_format: str):
    stocks = await report_services.get_critical_stocks()

    if not stocks:
        await message.answer("Критических остатков нет", reply_markup=kb.reports_kb)
    elif file_format == "excel":
        rows = await report_services.add_warehouse_details(stocks)
        await message.answer_document(report_excel.build_stocks_file(rows, "critical_stocks.xlsx"))
    else:
        blocks = ["Критические остатки"] + report_view.format_stocks(stocks)
        await send_long_text(message, blocks, "critical_stocks.txt", kb.reports_kb)


async def send_week_operations(message: Message, file_format: str):
    operations = await report_services.get_operations(WEEK_DAYS)

    if not operations:
        await message.answer("За неделю операций нет", reply_markup=kb.reports_kb)
    elif file_format == "excel":
        await message.answer_document(report_excel.build_operations_file(operations))
    else:
        blocks = ["Операции за неделю"] + [report_view.format_operation(item) for item in operations]
        await send_long_text(message, blocks, "operations.txt", kb.reports_kb)


REPORT_SENDERS = {
    "stocks": send_stocks,
    "critical": send_critical_stocks,
    "operations": send_week_operations,
}


@router.callback_query(F.data.startswith("report:"), IsAdmin())
async def send_report(callback: CallbackQuery):
    await callback.answer()
    _, report, file_format = callback.data.split(":")

    try:
        await REPORT_SENDERS[report](callback.message, file_format)
    except ServiceError as e:
        await callback.message.answer(e.message_to_user, reply_markup=kb.reports_kb)
