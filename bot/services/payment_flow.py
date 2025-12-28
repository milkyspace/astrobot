from bot.services.db import Db
from bot.services.user_service import UserService
from bot.services.order_service import OrderService
from bot.services.payment_service import PaymentService
from bot.services.yookassa_service import YooKassaService
from bot.config import settings
from bot.models.dto import UserDTO
from bot.services.exceptions import (
        OrderNotFoundError,
        UnknownOrderTypeError,
        PaymentGatewayError,
    )

import logging
logger = logging.getLogger(__name__)

class PaymentFlow:
    def __init__(self, db: Db):
        self.users = UserService(db)
        self.orders = OrderService(db)
        self.payments = PaymentService(db)
        self.yk = YooKassaService()

    def create_payment_for_user(self, tg_user: UserDTO) -> str:
        user = self.users.get_or_create(
            tg_id=tg_user.tg_id,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name
        )

        order = self.orders.get_last_unpaid_order(user.tg_id)
        if not order:
            raise OrderNotFoundError("Unpaid order not found", user)

        order_type = self.orders.get_type(order["id"])
        if order_type not in settings.PRICES:
            raise UnknownOrderTypeError(f"Unknown order type: {order_type}", order["id"], order)

        amount = settings.PRICES[order_type]

        pid, url = self.yk.create_payment(
            amount,
            f"Оплата услуги: {order_type}"
        )

        if not pid or not url:
            raise PaymentGatewayError("YooKassa payment creation failed")

        self.payments.create_payment(order["id"], pid, amount, url)

        # ОЧЕРЕДЬ ПРОВЕРКИ ОПЛАТЫ
        import os
        from datetime import timedelta
        from rq import Queue
        from redis import Redis
        from worker.tasks import wait_for_payment
        redis_conn = Redis(
            host=os.getenv("REDIS_HOST"),
            port=int(os.getenv("REDIS_PORT", 6379)),
        )
        payments_queue = Queue("payments", connection=redis_conn)
        CHECK_DELAY_SECONDS = int(os.getenv("PAYMENT_CHECK_DELAY", 30))  # раз в 30 сек
        payments_queue.enqueue_in(
            timedelta(seconds=CHECK_DELAY_SECONDS),
            wait_for_payment,
            pid,
            order["id"],
            user.tg_id,
        )
        # ОЧЕРЕДЬ ПРОВЕРКИ ОПЛАТЫ

        return url
