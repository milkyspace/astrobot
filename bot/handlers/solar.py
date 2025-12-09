from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.states.solar_states import SolarForm
from bot.keyboards.confirmation import confirm_keyboard, after_confirm_keyboard
from bot.utils.validators import validate_date, validate_time
from bot.models.dto import OrderItemDTO

from bot.services.db import Db
from bot.services.user_service import UserService
from bot.services.order_service import OrderService

router = Router()


# 1. Дата рождения
@router.message(SolarForm.birth_date)
async def solar_birth_date(message: Message, state: FSMContext):
    if not validate_date(message.text):
        await message.answer("Введите дату рождения в формате ДД.ММ.ГГГГ")
        return

    await state.update_data(birth_date=message.text)
    await state.set_state(SolarForm.birth_time)
    await message.answer("Введите время рождения (например: 15:30):")


# 2. Время рождения
@router.message(SolarForm.birth_time)
async def solar_birth_time(message: Message, state: FSMContext):
    if not validate_time(message.text):
        await message.answer("Введите время в формате ЧЧ:ММ")
        return

    await state.update_data(birth_time=message.text)
    await state.set_state(SolarForm.birth_city)
    await message.answer("Введите город рождения:")


# 3. Город рождения
@router.message(SolarForm.birth_city)
async def solar_birth_city(message: Message, state: FSMContext):
    await state.update_data(birth_city=message.text)
    await state.set_state(SolarForm.living_city)
    await message.answer("Введите город проживания в 2026 году:")


# 4. Город проживания в 2026
@router.message(SolarForm.living_city)
async def solar_living_city(message: Message, state: FSMContext):
    await state.update_data(living_city=message.text)

    data = await state.get_data()

    text = (
        "Пожалуйста, проверьте введённые данные:\n\n"
        f"📅 Дата рождения: {data['birth_date']}\n"
        f"⏰ Время рождения: {data['birth_time']}\n"
        f"📍 Город рождения: {data['birth_city']}\n"
        f"🏠 Город проживания в 2026: {data['living_city']}\n\n"
        "Всё верно?"
    )

    await state.set_state(SolarForm.confirm)
    await message.answer(text, reply_markup=after_confirm_keyboard())


# 5. Подтверждение данных
@router.message(SolarForm.confirm)
async def solar_confirm(message: Message, state: FSMContext):
    text = message.text

    if text == "✏ Изменить":
        await state.set_state(SolarForm.birth_date)
        await message.answer("Введите дату рождения заново:")
        return

    if text != "✅ Всё верно":
        await message.answer("Пожалуйста, подтвердите данные кнопкой.")
        return

    # Создаём заказ
    db = Db()
    users = UserService(db)
    orders = OrderService(db)

    user = users.get_or_create(
        tg_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    order = orders.create_order(user.id, "solar")

    data = await state.get_data()

    orders.save_order_data(
        order.id,
        OrderItemDTO(
            birth_date=data["birth_date"],
            birth_time=data["birth_time"],
            birth_city=data["birth_city"],
            extra_data={"living_city": data["living_city"]}
        )
    )

    # Кладём данные заказа в FSM,
    # чтобы следующий шаг (оплата) знал order_id и тип заказа
    await state.update_data(order_id=order.id, order_type="solar")

    await state.clear()

    await message.answer(
        "Данные успешно сохранены.\nТеперь можно оплатить заказ.",
        reply_markup=after_confirm_keyboard()
    )
