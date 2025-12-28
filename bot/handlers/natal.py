from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.states.natal_states import NatalForm
from bot.keyboards.natal import natal_confirm_keyboard, natal_pay_keyboard
from bot.utils.validators import validate_date, validate_time
from bot.models.dto import OrderItemDTO

from bot.services.db import Db
from bot.services.user_service import UserService
from bot.services.order_service import OrderService
from bot.services.payment_flow import PaymentFlow
from bot.services.exceptions import PaymentError

router = Router()

@router.callback_query(F.data == "action:natal:start")
async def natal_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(NatalForm.birth_date)

    await callback.message.edit_text(
        "Введите дату рождения (ДД.ММ.ГГГГ):"
    )
    await callback.answer()

@router.message(NatalForm.birth_date)
async def natal_birth_date(message: Message, state: FSMContext):
    if not validate_date(message.text):
        await message.answer("Введите дату в формате ДД.ММ.ГГГГ")
        return

    await state.update_data(birth_date=message.text)
    await state.set_state(NatalForm.birth_time)

    await message.answer("Введите время рождения (ЧЧ:ММ):")

@router.message(NatalForm.birth_time)
async def natal_birth_time(message: Message, state: FSMContext):
    if not validate_time(message.text):
        await message.answer("Введите время в формате ЧЧ:ММ")
        return

    await state.update_data(birth_time=message.text)
    await state.set_state(NatalForm.birth_city)

    await message.answer("Введите город рождения:")

@router.message(NatalForm.birth_city)
async def natal_birth_city(message: Message, state: FSMContext):
    await state.update_data(birth_city=message.text)
    data = await state.get_data()

    text = (
        "Проверьте данные:\n\n"
        f"📅 {data['birth_date']}\n"
        f"⏰ {data['birth_time']}\n"
        f"📍 {data['birth_city']}"
    )

    await state.set_state(NatalForm.confirm)

    await message.answer(
        text,
        reply_markup=natal_confirm_keyboard()
    )

@router.callback_query(F.data == "natal:confirm:edit")
async def natal_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NatalForm.birth_date)

    await callback.message.edit_text(
        "Введите дату рождения заново (ДД.ММ.ГГГГ):"
    )
    await callback.answer()

@router.callback_query(F.data == "natal:confirm:yes")
async def natal_confirm(callback: CallbackQuery, state: FSMContext):
    db = Db()
    users = UserService(db)
    orders = OrderService(db)

    user = users.get_or_create(
        tg_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name
    )

    data = await state.get_data()

    order_id = orders.create_order(user.id, "natal")

    orders.save_order_data(
        order_id,
        OrderItemDTO(
            birth_date=data["birth_date"],
            birth_time=data["birth_time"],
            birth_city=data["birth_city"],
            extra_data={}
        )
    )

    await state.clear()

    payment_flow = PaymentFlow(db)

    try:
        url = payment_flow.create_payment_for_user(user)
    except PaymentError:
        await callback.message.edit_text(
            "Не удалось создать платёж. Попробуйте позже."
        )
        await callback.answer()
        return

    await callback.message.edit_text(
        "Данные сохранены.\nТеперь можно оплатить заказ:",
        reply_markup=natal_pay_keyboard(url)
    )
    await callback.answer()