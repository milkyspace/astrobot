import uuid
import os
from yookassa import Configuration, Payment
from typing import Tuple


class YooKassaService:
    """
    Сервис обёртка над YooKassa SDK.
    Создание платежей и проверка статусов.
    """

    def __init__(self):
        Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
        Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")

    def create_payment(self, amount: int, description: str) -> Tuple[str, str]:
        """
        Создаёт платёж и возвращает:
        - payment_id
        - confirmation_url
        """

        payment = Payment.create({
            "amount": {
                "value": str(amount),
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": os.getenv("YOOKASSA_RETURN_URL")
            },
            "capture": True,
            "description": description
        }, uuid.uuid4())

        return payment.id, payment.confirmation.confirmation_url

    def get_payment_status(self, payment_id: str) -> str:
        """
        Получение статуса платежа с сервера YooKassa.
        """
        payment = Payment.find_one(payment_id)
        return payment.status
