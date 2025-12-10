from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def confirm_inline():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Всё верно", callback_data="confirm_ok")],
        [InlineKeyboardButton(text="✏ Изменить", callback_data="confirm_edit")],
    ])


def after_confirm_inline():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить заказ", callback_data="pay_now")],
        [InlineKeyboardButton(text="✏ Изменить", callback_data="confirm_edit")],
    ])
