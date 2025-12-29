from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def karma_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно", callback_data="karma:confirm:yes")],
            [InlineKeyboardButton(text="✏ Изменить", callback_data="karma:confirm:edit")],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="action:main_menu")],
        ]
    )


def karma_pay_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить заказ", url=url)],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="action:main_menu")],
        ]
    )
