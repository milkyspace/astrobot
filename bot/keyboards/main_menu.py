from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    """
    Главное меню — пользователь выбирает тип услуги.
    """
    kb = ReplyKeyboardBuilder()

    kb.button(text="🔮 Натальная карта")
    kb.button(text="✨ Кармические задачи")
    kb.button(text="🌞 Соляр на 2026 год")

    kb.adjust(1)

    return kb.as_markup(resize_keyboard=True)
