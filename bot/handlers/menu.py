from aiogram import Router, F
from aiogram.types import Message
from bot.keyboards.main_menu import main_menu
from aiogram.fsm.context import FSMContext

from bot.states.natal_states import NatalForm
from bot.states.karma_states import KarmaForm
from bot.states.solar_states import SolarForm

router = Router()

@router.message(F.text.in_([
    "🔮 Натальная карта",
    "✨ Кармические задачи",
    "🌞 Соляр на 2026 год"
]))
async def menu_handler(message: Message, state: FSMContext):
    """
    Пользователь выбрал услугу → запускаем FSM сбора данных.
    """

    selection = message.text

    if selection == "🔮 Натальная карта":
        await state.set_state(NatalForm.birth_date)
        await message.answer("Введите дату рождения (например: 12.04.1991):")
        return

    if selection == "✨ Кармические задачи":
        await state.set_state(KarmaForm.birth_date)
        await message.answer("Введите дату рождения:")
        return

    if selection == "🌞 Соляр на 2026 год":
        await state.set_state(SolarForm.birth_date)
        await message.answer("Введите дату рождения:")
        return

    await message.answer("Не понял выбор, попробуйте снова.", reply_markup=main_menu())
