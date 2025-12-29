from datetime import datetime
from typing import Optional, Union
from bot.services.db import Db

from bot.models.dto import PaymentDTO


class PaymentService:
    """
    Сервис управления платежами YooKassa.
    """

    def __init__(self, db: Db):
        self.db = db

    def create_payment(
            self, order_id: int, yookassa_id: str, amount: int, url: str
    ) -> PaymentDTO:
        payment = self.db.execute_returning(
            """
            INSERT INTO payments (order_id, yookassa_id, amount, url, status)
            VALUES (%s, %s, %s, %s, 'pending')
            RETURNING id, order_id, yookassa_id, amount, url, status
            """,
            (order_id, yookassa_id, amount, url)
        )

        return PaymentDTO(**payment)

    def update_status(self, yookassa_id: str, status: str) -> None:
        self.db.execute(
            "UPDATE payments SET status=%s WHERE yookassa_id=%s",
            (status, yookassa_id)
        )

    def get_payment(self, yookassa_id: str) -> Optional[PaymentDTO]:
        payment = self.db.fetch_one(
            "SELECT * FROM payments WHERE yookassa_id=%s",
            (yookassa_id,)
        )

        if not payment:
            return None

        return PaymentDTO(
            id=payment["id"],
            order_id=payment["order_id"],
            yookassa_id=payment["yookassa_id"],
            amount=payment["amount"],
            status=payment["status"],
            url=payment["url"],
            created_at=to_datetime(payment["created_at"]),
        )


def to_datetime(value: Union[datetime, str, None]) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        return datetime.fromisoformat(value)

    raise TypeError(f"Unsupported datetime type: {type(value)}")
