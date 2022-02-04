from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


menu = InlineKeyboardMarkup(row_width=1).add(
    InlineKeyboardButton(text="Добавить в отслеживание", callback_data="add")
)


def subscribe():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="1 месяц 390р", callback_data="day"),
        InlineKeyboardButton(text="1 год 4100р", callback_data="month")
    )
    return kb


def paid():
    kb = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Оплатил(а)", callback_data="paid")
    )
    return kb
