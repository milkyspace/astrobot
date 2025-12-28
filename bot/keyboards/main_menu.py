from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> InlineKeyboardMarkup:
    """
    Главное меню — пользователь выбирает тип услуги.
    """
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔮 Натальная карта", callback_data="action:natal:start")],
        [InlineKeyboardButton(text="✨ Кармические задачи", callback_data="action:karma:start")],
        [InlineKeyboardButton(text="🌞 Соляр на 2026 год", callback_data="action:solar:start")],
    ])

    return kb
