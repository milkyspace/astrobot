from typing import Optional
from .db import Db
from bot.models.dto import OrderDTO, OrderItemDTO


class OrderService:
    """
    Управление заказами:
    - создание заказа
    - обновление статуса
    - сохранение данных клиента
    """

    def __init__(self, db: Db):
        self.db = db

    def create_order(self, user_id: int, order_type: str) -> OrderDTO:
        new_order = self.db.execute_returning(
            """
            INSERT INTO orders (user_id, type, status)
            VALUES (%s, %s, 'pending')
            RETURNING id, user_id, type, status, result
            """,
            (user_id, order_type)
        )
        return OrderDTO(**new_order)

    def save_order_data(self, order_id: int, data: OrderItemDTO) -> None:
        self.db.execute(
            """
            INSERT INTO order_items (order_id, birth_date, birth_time, birth_city, extra_data)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                order_id,
                data.birth_date,
                data.birth_time,
                data.birth_city,
                data.extra_data,
            )
        )

    def update_status(self, order_id: int, new_status: str) -> None:
        self.db.execute(
            "UPDATE orders SET status=%s WHERE id=%s",
            (new_status, order_id)
        )

    def save_result(self, order_id: int, text: str) -> None:
        self.db.execute(
            "UPDATE orders SET result=%s WHERE id=%s",
            (text, order_id)
        )
