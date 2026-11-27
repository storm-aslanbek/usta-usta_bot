"""Текст отчетов для чата. Каждая функция возвращает список блоков"""
import html
from itertools import groupby

from handlers.history_view import COMMENT_MAX_LENGTH


OPERATION_TITLES = {"incoming": "Приход", "outgoing": "Расход", "transfer": "Перевод"}


def _group_by_warehouse(rows):
    # Строки из БД уже отсортированы по складу
    return groupby(rows, key=lambda row: row["warehouse"])


def format_stocks(rows) -> list[str]:
    blocks = []

    for warehouse, stocks in _group_by_warehouse(rows):
        lines = [
            f'{html.escape(stock["product"])}: {stock["quantity"]}'
            for stock in stocks if stock["product"]
        ]
        blocks.append("\n".join([f"<b>{html.escape(warehouse)}</b>"] + (lines or ["Товаров пока нет"])))

    return blocks


def format_total_stocks(totals) -> str:
    lines = [f'{html.escape(total["product"])}: {total["quantity"]}' for total in totals]
    return "\n".join(["<b>Всего по всем складам</b>"] + lines)


def format_operation(operation) -> str:
    route = html.escape(operation["warehouse"])
    if operation["operation_type"] == "transfer":
        route += f' → {html.escape(operation["recipient_warehouse"])}'

    text = (
        f'{operation["created_at"]:%d.%m.%Y %H:%M} · {OPERATION_TITLES[operation["operation_type"]]} · {route}\n'
        f'{html.escape(operation["product"])}: {operation["quantity"]}\n'
        f'Кто: {html.escape(operation["author"])}'
    )

    comment = operation["comment"]
    if comment and comment != "0":
        text += f'\nКомментарий: {html.escape(comment[:COMMENT_MAX_LENGTH])}'

    return text
