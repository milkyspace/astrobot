import os
import time
import random

from aiogram import Bot
from redis import Redis

from bot.services.db import Db
from bot.services.order_service import OrderService
from bot.services.payment_service import PaymentService
from bot.services.gpt_service import GPTService
from bot.services.progress_messages import PROGRESS_MESSAGES
from bot.models.dto import OrderDTO

from bot.services.yookassa_service import YooKassaService


# 📌 Telegram Bot для worker-а
bot = Bot(token=os.getenv("BOT_TOKEN"))


# =====================================================================
# 1) WAIT FOR PAYMENT (polling YooKassa)
# =====================================================================

def wait_for_payment(payment_id: str, order_id: int, chat_id: int):
    """
    Постоянно проверяет статус платежа.
    Когда статус меняется на 'succeeded' — запускаем обработку заказа.
    """

    db = Db()
    payments = PaymentService(db)
    orders = OrderService(db)
    yk = YooKassaService()

    bot_sync = bot  # просто чтобы читалось

    bot_sync.send_message(chat_id, "⏳ Ожидаю подтверждение оплаты...")

    while True:
        status = yk.get_payment_status(payment_id)

        # обновляем статус в БД
        payments.update_status(payment_id, status)

        if status == "succeeded":
            bot_sync.send_message(chat_id, "💰 Оплата получена! Начинаю расчёт ✨")

            orders.update_status(order_id, "processing")

            # запускаем следующую задачу → полный расчёт
            from rq import Queue
            redis_conn = Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"))
            queue = Queue("calculations", connection=redis_conn)

            queue.enqueue(full_calculation, order_id, chat_id)

            break

        elif status in ("canceled", "refunded"):
            bot_sync.send_message(chat_id, "❌ Платёж отменён.")
            orders.update_status(order_id, "failed")
            break

        time.sleep(5)  # раз в 5 сек опрашиваем YooKassa


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
    order_row = db.fetchone("SELECT * FROM orders WHERE id=%s", (order_id,))
    order = OrderDTO(**order_row)

    item = db.fetchone("SELECT * FROM order_items WHERE order_id=%s", (order_id,))

    birth_date = item["birth_date"]
    birth_time = item["birth_time"]
    birth_city = item["birth_city"]

    extra = item["extra_data"]

    # ======================================================
    # Выбираем промпт
    # ======================================================
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
    bot.send_message(chat_id, "✨ Начинаю глубокий астрологический анализ...")

    min_interval = int(os.getenv("PROGRESS_MIN_INTERVAL", 20))
    max_interval = int(os.getenv("PROGRESS_MAX_INTERVAL", 40))

    total_progress_messages = random.randint(7, 12)

    for i in range(total_progress_messages):
        msg = random.choice(PROGRESS_MESSAGES)
        bot.send_message(chat_id, msg)
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
    bot.send_message(chat_id, "🔮 Завершаю анализ...")

    result_text = gpt.generate(prompt)

    # сохраняем результат
    orders.save_result(order_id, result_text)
    orders.update_status(order_id, "done")

    # ======================================================
    # 4. Отправка результата
    # ======================================================
    bot.send_message(chat_id, "✨ Ваш расчёт готов! Отправляю:")
    bot.send_message(chat_id, result_text)
