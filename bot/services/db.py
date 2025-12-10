import psycopg2
import psycopg2.extras
from bot.config import settings


class Db:
    """
    Обёртка над psycopg2 для удобного доступа к БД.
    """

    def __init__(self):
        self.conn = psycopg2.connect(settings.DATABASE_URL)
        self.conn.autocommit = True

    def fetch_one(self, query: str, params: tuple = ()):
        """
        Выполняет запрос и возвращает одну строку в виде dict или None.
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()  # ← ИСПРАВЛЕНО
            return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()):
        """
        Возвращает список строк в виде list[dict]
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    def execute(self, query: str, params: tuple = ()):
        """
        Выполняет запрос без возврата значений.
        """
        with self.conn.cursor() as cur:
            cur.execute(query, params)

    def execute_returning(self, query: str, params: tuple = ()):
        """
        Выполняет INSERT ... RETURNING и возвращает dict одной строки
        """
        with self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return dict(row) if row else None
