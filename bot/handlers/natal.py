from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states.natal_states import NatalForm
from bot.keyboards.confirmation import confirm_keyboard, after_confirm_keyboard
from bot.utils.validators import validate_date, validate_time
from bot.models.dto import OrderItemDTO

from bot.services.db import Db
from bot.services.user_service import UserService
from bot.services.order_service import OrderService

router = Router()


@router.message(NatalForm.birth_date)
async def natal_birth_date(message: Message, state: FSMContext):
    if not validate_date(message.text):
        await message.answer("Введите дату в формате ДД.ММ.ГГГГ")
        return

    await state.update_data(birth_date=message.text)
    await state.set_state(NatalForm.birth_time)
    await message.answer("Введите время рождения (например: 14:20):")


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
        f"📅 Дата рождения: {data['birth_date']}\n"
        f"⏰ Время рождения: {data['birth_time']}\n"
        f"📍 Город рождения: {data['birth_city']}\n\n"
        "Всё верно?"
    )

    await state.set_state(NatalForm.confirm)
    await message.answer(text, reply_markup=confirm_keyboard())


@router.message(F.text == "✅ Всё верно")
async def natal_confirm(message: Message, state: FSMContext):
    db = Db()
    orders = OrderService(db)
    users = UserService(db)

    user = users.get_or_create(
        tg_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    data = await state.get_data()

    # 1️⃣ создаём заказ
    order_id = orders.create_order(user.id, "natal")

    # 2️⃣ сохраняем введённые данные
    orders.save_order_data(
        order_id=order_id,
        birth_date=data["birth_date"],
        birth_time=data["birth_time"],
        birth_city=data["birth_city"],
        extra_data={}
    )

    # 3️⃣ очищаем состояние
    await state.clear()

    await message.answer(
        "Данные успешно сохранены.\nТеперь можно оплатить заказ."
    )