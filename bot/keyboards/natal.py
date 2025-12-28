from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def natal_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно", callback_data="natal:confirm:yes")],
            [InlineKeyboardButton(text="✏ Изменить", callback_data="natal:confirm:edit")],
        ]
    )


def natal_pay_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить заказ", url=url)],
        ]
    )
