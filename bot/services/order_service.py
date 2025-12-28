from typing import Optional
from .db import Db
from bot.models.dto import OrderDTO, OrderItemDTO
import json


class OrderService:
    """
    Управление заказами:
    - создание заказа
    - обновление статуса
    - сохранение данных клиента
    """

    def __init__(self, db: Db):
        self.db = db

    def create_order(self, tg_id: int, order_type: str) -> int:
        """
        Создаёт заказ и возвращает ID.
        """
        row = self.db.fetch_one(
            """
            INSERT INTO orders (tg_id, type, status)
            VALUES (%s, %s, 'pending')
            RETURNING id
            """,
            (tg_id, order_type)
        )
        return row.get('id')

    def save_order_data(self, order_id, order_item_dto: OrderItemDTO):
        """
        Сохраняет данные клиента в order_items.
        """
        birth_date = order_item_dto.birth_date
        birth_time = order_item_dto.birth_time
        birth_city = order_item_dto.birth_city
        extra_data = order_item_dto.extra_data

        self.db.execute(
            """
            INSERT INTO order_items (order_id, birth_date, birth_time, birth_city, extra_data)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                order_id,
                birth_date,
                birth_time,
                birth_city,
                json.dumps(extra_data)
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

    def get_last_unpaid_order(self, tg_id: int):
        """
        Возвращает ID последнего неоплаченного заказа.
        """
        return self.db.fetch_one(
            """
            SELECT id FROM orders
            WHERE tg_id = %s AND status = 'pending'
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (tg_id,)
        )

    def get_type(self, order_id: int):
        row = self.db.fetch_one(
            "SELECT type FROM orders WHERE id = %s",
            (order_id,)
        )
        return row.get("type")

    def get_ui_message_id(self, order_id: int):
        row = self.db.fetch_one(
            "SELECT ui_message_id FROM orders WHERE id = %s",
            (order_id,)
        )
        return row.get("ui_message_id")

    def set_ui_message_id(self, order_id: int, message_id: int):
        self.db.execute(
            "UPDATE orders SET ui_message_id=%s WHERE id=%s",
            (message_id, order_id)
        )

    def update_ui(self, order_id: int, text: str):
        import datetime
        self.db.execute(
            """
            UPDATE orders
            SET ui_text = %s,
                ui_updated_at = %s
            WHERE id = %s
            """,
            (text, datetime.utcnow(), order_id)
        )

    def get_orders_with_pending_ui(self):
        return self.db.fetch_all(
            """
            SELECT *
            FROM orders
            WHERE ui_text IS NOT NULL
              AND (ui_synced IS NULL OR ui_synced = false)
            """
        )