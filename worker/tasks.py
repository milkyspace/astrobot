import os
import time
import random
from datetime import datetime, timedelta
from typing import Optional

from rq import Queue
from redis import Redis

from bot.services.db import Db
from bot.services.order_service import OrderService
from bot.services.payment_service import PaymentService
from bot.services.gpt_service import GPTService
from bot.services.yookassa_service import YooKassaService
from bot.services.progress_messages import PROGRESS_MESSAGES


# ======================================================
# 1) WAIT FOR PAYMENT (ОДИН ШАГ, БЕЗ LOOP)
# ======================================================

def wait_for_payment(payment_id: Optional[str], order_id: int, chat_id: int):
    CHECK_DELAY = int(os.getenv("PAYMENT_CHECK_DELAY", 30))
    TIMEOUT = int(os.getenv("PAYMENT_TIMEOUT", 3600))

    db = Db()
    orders = OrderService(db)
    payments = PaymentService(db)
    yk = YooKassaService()

    redis = Redis(
        host=os.getenv("REDIS_HOST"),
        port=int(os.getenv("REDIS_PORT", 6379)),
    )

    payments_q = Queue("payments", connection=redis)
    calc_q = Queue("calculations", connection=redis)

    if not payment_id:
        orders.update_status(order_id, "failed")
        orders.update_ui(order_id, "❌ Ошибка платежа.")
        return

    payment = payments.get_payment(payment_id)
    if not payment:
        orders.update_status(order_id, "failed")
        orders.update_ui(order_id, "❌ Платёж не найден.")
        return

    created_at = payment["created_at"]
    if datetime.utcnow() - created_at > timedelta(seconds=TIMEOUT):
        orders.update_status(order_id, "expired")
        orders.update_ui(
            order_id,
            "⌛ Время ожидания оплаты истекло.\nОформите заказ заново."
        )
        return

    try:
        status = yk.get_payment_status(payment_id)
    except Exception:
        payments_q.enqueue_in(
            timedelta(seconds=CHECK_DELAY),
            wait_for_payment,
            payment_id,
            order_id,
            chat_id,
        )
        return

    payments.update_status(payment_id, status)

    if status == "succeeded":
        orders.update_status(order_id, "processing")
        orders.update_ui(
            order_id,
            "💰 Оплата получена!\n🔮 Начинаю астрологический расчёт…"
        )
        calc_q.enqueue(full_calculation, order_id, chat_id)
        return

    if status in ("canceled", "refunded"):
        orders.update_status(order_id, "failed")
        orders.update_ui(order_id, "❌ Платёж отменён.")
        return

    payments_q.enqueue_in(
        timedelta(seconds=CHECK_DELAY),
        wait_for_payment,
        payment_id,
        order_id,
        chat_id,
    )


# ======================================================
# 2) FULL CALCULATION
# ======================================================

def full_calculation(order_id: int, chat_id: int):
    db = Db()
    orders = OrderService(db)
    gpt = GPTService()

    order = db.fetch_one("SELECT * FROM orders WHERE id=%s", (order_id,))
    item = db.fetch_one(
        "SELECT * FROM order_items WHERE order_id=%s", (order_id,)
    )

    birth_date = item["birth_date"]
    birth_time = item["birth_time"]
    birth_city = item["birth_city"]

    prompt = (
        "Ты профессиональный астролог мирового уровня.\n"
        f"Дата рождения: {birth_date}\n"
        f"Время: {birth_time}\n"
        f"Город: {birth_city}"
    )

    orders.update_ui(order_id, "✨ Начинаю глубокий анализ…")

    for _ in range(random.randint(7, 12)):
        orders.update_ui(order_id, random.choice(PROGRESS_MESSAGES))
        time.sleep(random.randint(20, 40))

    time.sleep(random.randint(480, 720))

    orders.update_ui(order_id, "🔮 Завершаю анализ…")

    result = gpt.generate(prompt)

    orders.save_result(order_id, result)
    orders.update_status(order_id, "done")
    orders.update_ui(order_id, f"✨ Ваш расчёт готов!\n\n{result}")