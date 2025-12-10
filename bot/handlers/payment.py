from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.services.db import Db
from bot.services.user_service import UserService
from bot.services.order_service import OrderService
from bot.services.yookassa_service import YooKassaService
from bot.config import settings

router = Router()


@router.message(F.text == "💳 Оплатить заказ")
async def process_payment(message: Message, state: FSMContext):
    db = Db()
    users = UserService(db)
    orders = OrderService(db)
    yk = YooKassaService(db)

    # текущий пользователь
    user = users.get_or_create(
        tg_id=message.from_user.id,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    # ищем неоплаченный заказ
    row = orders.get_last_unpaid_order(user.id)
    if not row:
        await message.answer("Ошибка: не найден заказ. Попробуйте снова.")
        return

    order_id = row[0]

    # определяем цену услуги
    order_type = orders.get_type(order_id)
    amount = settings.PRICES[order_type]     # например {'natal':150, 'karma':200, ...}
    description = f"Оплата услуги: {order_type}"

    # создаём платёж
    payment = yk.create_payment(order_id, amount, description)

    await message.answer(
        f"💳 Стоимость: {payment.amount['value']} ₽\n\n"
        f"Для оплаты перейдите по ссылке:\n{payment.confirmation.confirmation_url}"
    )
