import os
import psycopg2
from psycopg2.extras import DictCursor
from typing import Any, List


class Db:
    """
    Класс для подключения к PostgreSQL и выполнения SQL запросов.
    Принцип SRP: класс занимается только работой с БД.
    """

    def __init__(self):
        self.conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            cursor_factory=DictCursor
        )
        self.conn.autocommit = True

    def fetchone(self, query: str, params: tuple = ()) -> Any:
        """Возвращает одну запись."""
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()

    def fetchall(self, query: str, params: tuple = ()) -> List[Any]:
        """Возвращает список записей."""
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def execute(self, query: str, params: tuple = ()) -> None:
        """Выполняет SQL-запрос без возврата результата."""
        with self.conn.cursor() as cur:
            cur.execute(query, params)

    def execute_returning(self, query: str, params: tuple = ()) -> Any:
        """Выполняет SQL и возвращает RETURNING значение."""
        with self.conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchone()
