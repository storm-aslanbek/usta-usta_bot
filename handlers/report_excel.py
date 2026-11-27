"""Сборка Excel-файлов отчетов"""
from datetime import datetime
from io import BytesIO

from aiogram.types import BufferedInputFile
from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

from handlers.report_view import OPERATION_TITLES


DATE_FORMAT = "DD.MM.YYYY HH:MM"
MAX_COLUMN_WIDTH = 60


def _build_file(filename: str, headers: list[str], rows: list[list]) -> BufferedInputFile:
    workbook = Workbook()
    sheet = workbook.active

    for row_number, row in enumerate([headers] + rows, start=1):
        for column_number, value in enumerate(row, start=1):
            _write_cell(sheet.cell(row_number, column_number), value)

    for cell in sheet[1]:
        cell.font = Font(bold=True)
    sheet.freeze_panes = "A2"

    for column_number, column in enumerate(zip(headers, *rows), start=1):
        width = max(len(str(value)) for value in column if value is not None) + 2
        sheet.column_dimensions[get_column_letter(column_number)].width = min(width, MAX_COLUMN_WIDTH)

    buffer = BytesIO()
    workbook.save(buffer)
    return BufferedInputFile(buffer.getvalue(), filename=filename)


def _write_cell(cell, value):
    if isinstance(value, str):
        cell.value = ILLEGAL_CHARACTERS_RE.sub("", value)
        cell.data_type = "s"  # текст, начинающийся с "=", не должен стать формулой
        return

    cell.value = value
    if isinstance(value, datetime):
        cell.number_format = DATE_FORMAT


def _activity_columns(activity) -> list:
    if not activity:
        return [None, None, None]

    title = OPERATION_TITLES[activity["operation_type"]]
    if activity["operation_type"] == "transfer":
        title = "Входящий перевод" if activity["is_incoming_transfer"] else "Исходящий перевод"

    return [activity["created_at"], title, activity["author"]]


def build_stocks_file(rows, filename: str, totals=()) -> BufferedInputFile:
    headers = ["Склад", "Товар", "Остаток", "Пользователи склада",
               "Последняя активность", "Операция", "Автор"]

    table = [
        [row["warehouse"], row["product"], row["quantity"], row["responsible"]]
        + _activity_columns(row["last_activity"])
        for row in rows
    ]

    if totals:
        empty_row = [None] * len(headers)
        table.append(empty_row)
        for total in totals:
            total_row = ["Всего по всем складам", total["product"], total["quantity"]]
            table.append(total_row + empty_row[len(total_row):])

    return _build_file(filename, headers, table)


def build_operations_file(operations) -> BufferedInputFile:
    headers = ["Дата", "Операция", "Товар", "Количество", "Откуда", "Куда", "Автор", "Комментарий"]
    rows = []

    for operation in operations:
        operation_type = operation["operation_type"]
        sender = operation["warehouse"] if operation_type != "incoming" else None
        recipient = operation["warehouse"] if operation_type == "incoming" else operation["recipient_warehouse"]
        comment = operation["comment"] if operation["comment"] != "0" else None

        rows.append([
            operation["created_at"], OPERATION_TITLES[operation_type], operation["product"],
            operation["quantity"], sender, recipient, operation["author"], comment,
        ])

    return _build_file("operations.xlsx", headers, rows)
