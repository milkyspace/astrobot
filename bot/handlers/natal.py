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
from bot.keyboards.common import back_to_main_menu

router = Router()

@router.callback_query(F.data == "action:natal:start")
async def natal_start(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(NatalForm.birth_date)

    msg = await callback.message.edit_text(
        "Введите дату рождения (ДД.ММ.ГГГГ):",
        reply_markup=back_to_main_menu()
    )

    await state.update_data(ui_message_id=msg.message_id)
    await callback.answer()

@router.message(NatalForm.birth_date)
async def natal_birth_date(message: Message, state: FSMContext):
    if not validate_date(message.text):
        await message.delete()
        return

    data = await state.get_data()
    ui_message_id = data["ui_message_id"]

    await state.update_data(birth_date=message.text)
    await state.set_state(NatalForm.birth_time)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=ui_message_id,
        text="Введите время рождения (ЧЧ:ММ):",
        reply_markup=back_to_main_menu()
    )

    await message.delete()

@router.message(NatalForm.birth_time)
async def natal_birth_time(message: Message, state: FSMContext):
    if not validate_time(message.text):
        await message.delete()
        return

    data = await state.get_data()
    ui_message_id = data["ui_message_id"]

    await state.update_data(birth_time=message.text)
    await state.set_state(NatalForm.birth_city)

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=ui_message_id,
        text="Введите город рождения:",
        reply_markup=back_to_main_menu()
    )

    await message.delete()

@router.message(NatalForm.birth_city)
async def natal_birth_city(message: Message, state: FSMContext):
    data = await state.get_data()
    ui_message_id = data["ui_message_id"]

    await state.update_data(birth_city=message.text)
    await state.set_state(NatalForm.confirm)

    data = await state.get_data()

    text = (
        "Проверьте данные:\n\n"
        f"📅 {data['birth_date']}\n"
        f"⏰ {data['birth_time']}\n"
        f"📍 {data['birth_city']}"
    )

    await message.bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=ui_message_id,
        text=text,
        reply_markup=natal_confirm_keyboard(),
    )

    await message.delete()

@router.callback_query(F.data == "natal:confirm:edit")
async def natal_edit(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ui_message_id = data["ui_message_id"]

    await state.set_state(NatalForm.birth_date)

    await callback.message.bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=ui_message_id,
        text="Введите дату рождения заново (ДД.ММ.ГГГГ):",
        reply_markup=back_to_main_menu()
    )

    await callback.answer()

@router.callback_query(F.data == "natal:confirm:yes")
async def natal_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    ui_message_id = data["ui_message_id"]

    db = Db()
    users = UserService(db)
    orders = OrderService(db)

    user = users.get_or_create(
        tg_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name
    )

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
        await callback.message.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=ui_message_id,
            text="Не удалось создать платёж. Попробуйте позже.",
            reply_markup=back_to_main_menu()
        )
        await callback.answer()
        return

    await callback.message.bot.edit_message_text(
        chat_id=callback.message.chat.id,
        message_id=ui_message_id,
        text="Данные сохранены.\nТеперь можно оплатить заказ:",
        reply_markup=natal_pay_keyboard(url)
    )

    await callback.answer()