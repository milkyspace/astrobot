import time
import random
from aiogram import Bot
from datetime import datetime, timedelta
from typing import Optional
import os

from rq import Queue
from redis import Redis

from bot.config import settings
from bot.services.db import Db
from bot.services.order_service import OrderService
from bot.services.payment_service import PaymentService
from bot.services.gpt_service import GPTService
from bot.services.progress_messages import PROGRESS_MESSAGES
from bot.models.dto import OrderDTO
from bot.utils.async_helper import send_message

from bot.services.yookassa_service import YooKassaService

# 📌 Telegram Bot для worker-а
bot = Bot(token=os.getenv("BOT_TOKEN"))


# =====================================================================
# 1) WAIT FOR PAYMENT (polling YooKassa)
# =====================================================================


def wait_for_payment(payment_id: Optional[str], order_id: int, chat_id: int):
    """
    Проверяет статус платежа ОДИН раз.
    Если платёж не завершён — переenqueue себя позже.
    Никаких while / sleep.
    """

    CHECK_DELAY_SECONDS = int(os.getenv("PAYMENT_CHECK_DELAY", 30))  # раз в 30 сек
    MAX_WAIT_SECONDS = int(os.getenv("PAYMENT_TIMEOUT", 60 * 60))  # 30 минут

    db = Db()
    orders = OrderService(db)
    payments = PaymentService(db)
    yk = YooKassaService()

    redis_conn = Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT", 6379)),
    )

    payments_queue = Queue("payments", connection=redis_conn)
    calculations_queue = Queue("calculations", connection=redis_conn)

    # ======================================================
    # 🛡️ ADMIN MODE — сразу в расчёт
    # ======================================================
    if chat_id in settings.ADMIN_TG_IDS:
        orders.update_status(order_id, "processing")

        send_message(
            chat_id,
            "🛡️ Админ-режим: платёж подтверждён автоматически."
        )
        send_message(
            chat_id,
            "💰 Оплата получена!\n"
            "Начинаю астрологический расчёт ✨"
        )

        calculations_queue.enqueue(
            full_calculation,
            order_id,
            chat_id,
        )
        return

    # ======================================================
    # 👤 Нет payment_id — ошибка
    # ======================================================
    if not payment_id:
        orders.update_status(order_id, "failed")
        send_message(chat_id, "❌ Ошибка платежа. Попробуйте позже.")
        return

    # ======================================================
    # ⏳ Проверка таймаута ожидания
    # ======================================================
    payment = payments.get(payment_id)

    if payment is None:
        orders.update_status(order_id, "failed")
        send_message(chat_id, "❌ Платёж не найден.")
        return

    created_at = payment["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    if datetime.utcnow() - created_at > timedelta(seconds=MAX_WAIT_SECONDS):
        orders.update_status(order_id, "expired")

        send_message(
            chat_id,
            "⌛ Время ожидания оплаты истекло.\n"
            "Пожалуйста, оформите заказ заново."
        )
        return

    # ======================================================
    # 💳 Проверяем статус YooKassa
    # ======================================================
    try:
        status = yk.get_payment_status(payment_id)
    except Exception:
        payments_queue.enqueue_in(
            timedelta(seconds=CHECK_DELAY_SECONDS),
            wait_for_payment,
            payment_id,
            order_id,
            chat_id,
        )
        return

    payments.update_status(payment_id, status)

    # ======================================================
    # ✅ Платёж успешен → расчёт
    # ======================================================
    if status == "succeeded":
        orders.update_status(order_id, "processing")

        send_message(
            chat_id,
            "💰 Оплата получена!\n"
            "Начинаю астрологический расчёт ✨"
        )

        calculations_queue.enqueue(
            full_calculation,
            order_id,
            chat_id,
        )
        return

    # ======================================================
    # ❌ Платёж отменён
    # ======================================================
    if status in ("canceled", "refunded"):
        orders.update_status(order_id, "failed")

        send_message(
            chat_id,
            "❌ Платёж отменён или возвращён.\n"
            "Если это ошибка — попробуйте ещё раз."
        )
        return

    # ======================================================
    # 🔄 Всё ещё pending → проверим позже
    # ======================================================
    payments_queue.enqueue_in(
        timedelta(seconds=CHECK_DELAY_SECONDS),
        wait_for_payment,
        payment_id,
        order_id,
        chat_id,
    )


# =====================================================================
# 2) FULL CALCULATION (progress → delay → GPT → result)
# =====================================================================

def full_calculation(order_id: int, chat_id: int):
    """
    Полная обработка заказа:
    - шлём прогресс шаги
    - ждём случайную задержку
    - вызываем GPT
    - отправляем результат
    """

    db = Db()
    orders = OrderService(db)
    gpt = GPTService()

    # достаём данные заказа
    order_row = db.fetch_one("SELECT * FROM orders WHERE id=%s", (order_id,))
    order = OrderDTO(**order_row)

    item = db.fetch_one("SELECT * FROM order_items WHERE order_id=%s", (order_id,))

    birth_date = item["birth_date"]
    birth_time = item["birth_time"]
    birth_city = item["birth_city"]

    extra = item["extra_data"]

    # ======================================================
    # Выбираем промпт
    # ======================================================
    prompt = ""
    if order.type == "natal":
        prompt = (
            "Представь, что ты — профессиональный астролог мирового уровня...\n"
            f"Вот мои данные: {birth_date}, {birth_time}, {birth_city}."
        )

    elif order.type == "karma":
        prompt = (
            "Представь, что ты — астролог мирового уровня, эксперт по кармической астрологии...\n"
            f"Вот мои данные: {birth_date}, {birth_time}, {birth_city}."
        )

    elif order.type == "solar":
        living_city = extra.get("living_city")
        prompt = (
            "Ты — профессиональный астролог мирового уровня.\n"
            "Проанализируй мой соляр на 2026 год.\n"
            f"Дата рождения: {birth_date}, время: {birth_time}, город рождения: {birth_city}, "
            f"город проживания: {living_city}."
        )

    # ======================================================
    # 1. Отправляем прогресс-сообщения
    # ======================================================
    send_message(chat_id, "✨ Начинаю глубокий астрологический анализ...")

    min_interval = int(os.getenv("PROGRESS_MIN_INTERVAL", 20))
    max_interval = int(os.getenv("PROGRESS_MAX_INTERVAL", 40))

    total_progress_messages = random.randint(7, 12)

    for i in range(total_progress_messages):
        msg = random.choice(PROGRESS_MESSAGES)
        send_message(chat_id, msg)
        time.sleep(random.randint(min_interval, max_interval))

    # ======================================================
    # 2. Основная задержка (создание «ценности»)
    # ======================================================
    delay_min = int(os.getenv("DELAY_MIN", 480))
    delay_max = int(os.getenv("DELAY_MAX", 720))
    delay = random.randint(delay_min, delay_max)

    time.sleep(delay)

    # ======================================================
    # 3. GPT расчёт
    # ======================================================
    send_message(chat_id, "🔮 Завершаю анализ...")

    result_text = gpt.generate(prompt)

    # сохраняем результат
    orders.save_result(order_id, result_text)
    orders.update_status(order_id, "done")

    # ======================================================
    # 4. Отправка результата
    # ======================================================
    send_message(chat_id, "✨ Ваш расчёт готов! Отправляю:")
    send_message(chat_id, result_text)
