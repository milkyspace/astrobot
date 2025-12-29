from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from bot.keyboards.main_menu import main_menu

router = Router()


@router.callback_query(F.data == "action:main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()

    await callback.message.edit_text(
        "✨ Я ваш персональный астрологический помощник.\n"
        "Выберите услугу, которую хотите рассчитать:",
        reply_markup=main_menu()
    )

    await callback.answer()
