from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def back_to_main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⬅️ В главное меню", callback_data="action:main_menu")]
        ]
    )
