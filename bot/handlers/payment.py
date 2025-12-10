from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.services.db import Db
from bot.services.user_service import UserService
from bot.services.order_service import OrderService
from bot.services.yookassa_service import YooKassaService
from bot.config import settings

router = Router()


@router.callback_query(F.data == "pay_now")
async def process_payment(callback, state: FSMContext):
    db = Db()
    users = UserService(db)
    orders = OrderService(db)
    yk = YooKassaService(db)

    user = users.get_or_create(
        tg_id=callback.from_user.id,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name
    )

    # ищем неоплаченный заказ
    row = orders.get_last_unpaid_order(user.id)
    if not row:
        await callback.answer("Ошибка: заказ не найден", show_alert=True)
        return

    order_id = row["id"]
    order_type = orders.get_type(order_id)
    amount = settings.PRICES[order_type]

    payment = yk.create_payment(order_id, amount, f"Оплата услуги: {order_type}")

    await callback.message.edit_text(
        f"💳 Стоимость: {payment.amount['value']} ₽\n\n"
        f"Перейдите к оплате:\n{payment.confirmation.confirmation_url}"
    )