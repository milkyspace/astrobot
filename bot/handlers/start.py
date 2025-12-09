from aiogram import Router, F
from aiogram.types import Message
from bot.keyboards.main_menu import main_menu
from bot.services.db import Db
from bot.services.user_service import UserService

router = Router()

@router.message(F.text == "/start")
async def start_handler(message: Message):
    """
    Первый вход пользователя.
    Создаём или получаем пользователя.
    Показываем главное меню.
    """
    db = Db()
    users = UserService(db)

    users.get_or_create(
        tg_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    await message.answer(
        "Здравствуйте! ✨\n\n"
        "Я ваш персональный астрологический помощник.\n"
        "Выберите услугу, которую хотите рассчитать:",
        reply_markup=main_menu()
    )
