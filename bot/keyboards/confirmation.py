from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup
from uvloop.dns import callback


def confirm_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура подтверждения данных.
    """
    kb = ReplyKeyboardBuilder()

    kb.button(text="✅ Всё верно")
    kb.button(text="✏ Изменить")

    kb.adjust(1)

    return kb.as_markup(resize_keyboard=True)

def after_confirm_keyboard() -> ReplyKeyboardMarkup:
    kb = ReplyKeyboardBuilder()

    kb.button(text="💳 Оплатить заказ")
    kb.button(text="✏ Изменить")

    kb.adjust(1)
    return kb.as_markup(resize_keyboard=True)
