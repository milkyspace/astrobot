from typing import Optional
from .db import Db
from bot.models.dto import UserDTO


class UserService:
    """
    Логика работы с пользователями.
    Принцип SRP — сервис отвечает только за операции с users.
    """

    def __init__(self, db: Db):
        self.db = db

    def get_or_create(self, tg_id: int, first_name: str, last_name: str) -> UserDTO:
        user = self.db.fetch_one(
            "SELECT * FROM users WHERE tg_id=%s",
            (tg_id,)
        )

        if user:
            return UserDTO(**user)

        new_user = self.db.execute_returning(
            """
            INSERT INTO users (tg_id, first_name, last_name)
            VALUES (%s, %s, %s)
            RETURNING id, tg_id, first_name, last_name
            """,
            (tg_id, first_name, last_name)
        )

        return UserDTO(**new_user)
