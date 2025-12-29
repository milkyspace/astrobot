from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def solar_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Всё верно", callback_data="solar:confirm:yes")],
            [InlineKeyboardButton(text="✏ Изменить", callback_data="solar:confirm:edit")],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="action:main_menu")],
        ]
    )


def solar_pay_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить заказ", url=url)],
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="action:main_menu")],
        ]
    )
