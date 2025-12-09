from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from bot.services.db import Db
from bot.services.order_service import OrderService
from bot.services.payment_service import PaymentService
from bot.services.yookassa_service import YooKassaService

from redis import Redis
from rq import Queue
from worker.tasks import wait_for_payment

import os

router = Router()

PRICE_MAP = {
    "natal": int(os.getenv("PRICE_NATAL")),
    "karma": int(os.getenv("PRICE_KARMA")),
    "solar": int(os.getenv("PRICE_SOLAR")),
}

NAME_MAP = {
    "natal": "Натальная карта",
    "karma": "Кармические задачи",
    "solar": "Соляр на 2026 год",
}


@router.message(F.text == "💳 Оплатить заказ")
async def proceed_payment(message: Message, state: FSMContext):
    """
    Хэндлер запуска оплаты.
    Достаём из FSM ID заказа и его тип, создаём платёж, отправляем ссылку пользователю.
    После этого создаём RQ-задачу для отслеживания оплаты.
    """

    data = await state.get_data()
    order_id = data.get("order_id")
    order_type = data.get("order_type")

    if not order_id or not order_type:
        await message.answer("Ошибка: не найден заказ. Попробуйте снова.")
        await state.clear()
        return

    amount = PRICE_MAP[order_type]
    description = NAME_MAP[order_type]

    db = Db()
    order_service = OrderService(db)
    payment_service = PaymentService(db)
    yk = YooKassaService()

    # Создаём платёж в YooKassa
    payment_id, url = yk.create_payment(amount, description)

    # Сохраняем платёж в БД
    payment_service.create_payment(order_id, payment_id, amount, url)

    await message.answer(
        f"💳 Стоимость услуги: {amount} ₽\n"
        f"Для оплаты перейдите по ссылке:\n{url}\n\n"
        "После оплаты я автоматически начну расчёт ✨"
    )

    # Создаём RQ-задачу для отслеживания оплаты
    redis_conn = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))
    queue = Queue("payments", connection=redis_conn)

    queue.enqueue(
        wait_for_payment,
        payment_id,
        order_id,
        message.chat.id,
        job_timeout=600  # 10 минут
    )

    await state.clear()
