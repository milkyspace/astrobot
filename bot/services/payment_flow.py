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
            tg_id=tg_user.id,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name
        )

        order = self.orders.get_last_unpaid_order(user.tg_id)
        if not order:
            raise OrderNotFoundError("Unpaid order not found", user)

        order_type = self.orders.get_type(order["id"])
        if order_type not in settings.PRICES:
            raise UnknownOrderTypeError(f"Unknown order type: {order_type}")

        amount = settings.PRICES[order_type]

        pid, url = self.yk.create_payment(
            amount,
            f"Оплата услуги: {order_type}"
        )

        if not pid or not url:
            raise PaymentGatewayError("YooKassa payment creation failed")

        self.payments.create_payment(order["id"], pid, amount, url)
        return url
