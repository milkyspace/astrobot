import os
import uuid
from typing import Tuple

from yookassa import Configuration, Payment


class YooKassaService:
    """
    Сервис-обёртка над YooKassa.
    Отвечает только за создание платежей и получение их статуса.
    """

    def __init__(self) -> None:
        Configuration.account_id = os.getenv("YOOKASSA_SHOP_ID")
        Configuration.secret_key = os.getenv("YOOKASSA_SECRET_KEY")
        self.return_url = os.getenv("YOOKASSA_RETURN_URL", "https://t.me/your_bot")

    def create_payment(self, amount: int, description: str) -> Tuple[str, str]:
        """
        Создаёт платёж в YooKassa.

        :param amount: сумма в рублях
        :param description: описание платежа
        :return: (payment_id, confirmation_url)
        """
        payment = Payment.create(
            {
                "amount": {
                    "value": f"{amount}.00",
                    "currency": "RUB",
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": self.return_url,
                },
                "capture": True,
                "description": description,
            },
            uuid.uuid4().hex,
        )

        payment_id = payment.id
        confirmation_url = payment.confirmation.confirmation_url

        return payment_id, confirmation_url

    @staticmethod
    def get_payment_status(payment_id: str) -> str:
        """
        Возвращает статус платежа по его ID.
        """
        payment = Payment.find_one(payment_id)
        return payment.status
