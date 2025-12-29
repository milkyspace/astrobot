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

from bot.services.yookassa_service import YooKassaService
from worker.telegram import edit_message

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

    ui_message_id = orders.get_ui_message_id(order_id)

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

        edit_message(chat_id, ui_message_id, "💰 Оплата получена!\n"
                                             "Начинаю астрологический расчёт ✨")

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
        edit_message(chat_id, ui_message_id, "❌ Ошибка платежа. Попробуйте позже.")
        return

    # ======================================================
    # ⏳ Проверка таймаута ожидания
    # ======================================================
    payment = payments.get(payment_id)

    if payment is None:
        orders.update_status(order_id, "failed")
        edit_message(chat_id, ui_message_id, "❌ Платёж не найден.")

        return

    created_at = payment["created_at"]
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    if datetime.utcnow() - created_at > timedelta(seconds=MAX_WAIT_SECONDS):
        orders.update_status(order_id, "expired")

        edit_message(chat_id, ui_message_id, "Пожалуйста, оформите заказ заново.")

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

        edit_message(chat_id, ui_message_id, "💰 Оплата получена!\n"
                                             "Начинаю астрологический расчёт ✨")

        ui_message_id = orders.get_ui_message_id(order_id)
        edit_message(chat_id, ui_message_id, "💰 Оплата получена!\n\n"
                                             "🔮 Начинаю астрологический расчёт…")

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

        edit_message(chat_id, ui_message_id, "❌ Платёж отменён или возвращён.\n"
                                             "Если это ошибка — попробуйте ещё раз.")
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
    from worker.telegram import edit_message

    db = Db()
    orders = OrderService(db)
    gpt = GPTService()

    ui_message_id = orders.get_ui_message_id(order_id)

    order_row = db.fetch_one(
        "SELECT * FROM orders WHERE id=%s",
        (order_id,)
    )
    order = OrderDTO(**order_row)

    item = db.fetch_one(
        "SELECT * FROM order_items WHERE order_id=%s",
        (order_id,)
    )

    birth_date = item["birth_date"]
    birth_time = item["birth_time"]
    birth_city = item["birth_city"]
    extra = item["extra_data"]

    prompt_html = f"ВАЖНО:\n"
    f"Ты ОБЯЗАН вернуть результат СТРОГО в HTML для Telegram.)\n"
    f"Правила:\n"
    f"- Используй только теги: <b>, <i>, <u>, <code>, <pre>, <a>, <br>, <p>\n"
    f"- НЕ используй markdown\n"
    f"- НЕ используй списки <ul>/<li>\n"
    f"- Разделяй блоки через <br><br>\n"
    f"- Текст должен быть сразу готов к отправке в Telegram с parse_mode=HTML"

    prompt_end = f"Ты создаёшь ЗАВЕРШЁННЫЙ астрологический отчёт для клиента.\n"
    f"ВАЖНО:\n"
    f"- НЕ задавай вопросов\n"
    f"- НЕ предлагай продолжить диалог\n"
    f"- НЕ пиши фразы вида: 'если хотите', 'могу сделать', 'предлагаю', 'скажите'\n"
    f"- НЕ упоминай дополнительные услуги, расчёты или апселлы\n"
    f"- НЕ используй обращения к читателю в формате диалога\n"
    f"Отчёт должен заканчиваться УТВЕРЖДЕНИЯМИ и РЕКОМЕНДАЦИЯМИ, а не предложениями продолжить.\n"
    f"{prompt_html}"

    if order.type == "natal":
        prompt = (
            "Представь, что ты — профессиональный астролог мирового уровня...\n"
            f"Вот мои данные: дата рождения {birth_date}, время рождения {birth_time}, город рождения {birth_city}.\n"
            f"Создай полную натальную карту. Нужно описать все, что можно. Как можно больше информации. Расскажи всё.\n"
            f"{prompt_end}"
        )
    elif order.type == "karma":
        prompt = (
            "Представь, что ты — астролог мирового уровня...\n"
            f"Вот мои данные: дата рождения {birth_date}, время рождения {birth_time}, город рождения {birth_city}.\n"
            f"Создай отчет по моим кармическим задачам. Нужно описать все, что можно. Как можно больше информации. Расскажи всё."
            f"{prompt_end}"
        )
    else:
        living_city = extra.get("living_city")
        prompt = (
            "Ты — профессиональный астролог...\n"
            f"дата рождения {birth_date}, время рождения {birth_time}, город рождения {birth_city}, город проживания {living_city}.\n"
            f"Создай полный соляр на 2026 год. Нужно описать все, что можно. Как можно больше информации. Расскажи всё."
            f"{prompt_end}"
        )

    edit_message(chat_id, ui_message_id, "✨ Начинаю глубокий астрологический анализ...")

    # ======================================================
    # 🚀 GPT В ФОНЕ
    # ======================================================
    from concurrent.futures import ThreadPoolExecutor, Future

    def format_progress(pct: int, line: str) -> str:
        return f"<b>🔮 Выполняю расчёт</b>\n{line}\n\n<b>Готово:</b> {pct}%"

    def clamp(v: int, lo: int, hi: int) -> int:
        return lo if v < lo else hi if v > hi else v

    with ThreadPoolExecutor(max_workers=1) as executor:
        future: Future[str] = executor.submit(gpt.generate, prompt)

        edit_message(chat_id, ui_message_id, "🔮 Анализ запущен…")

        PROGRESS_INTERVAL = 3
        last_update = 0
        pct = 3
        max_wait_pct = random.randint(92, 97)

        while not future.done():
            now = time.time()
            if now - last_update >= PROGRESS_INTERVAL:
                line = random.choice(PROGRESS_MESSAGES)
                step = random.randint(1, 3)
                pct = clamp(pct + step, 3, max_wait_pct)
                edit_message(chat_id, ui_message_id, format_progress(pct, line))
                last_update = now
            time.sleep(0.25)

        edit_message(chat_id, ui_message_id, "🔮 Завершаю анализ…")

        result_text = future.result()

    # ======================================================
    # 💾 СОХРАНЕНИЕ
    # ======================================================
    orders.save_result(order_id, result_text)
    orders.update_status(order_id, "done")

    from worker.telegram import edit_message, send_message

    edit_message(
        chat_id,
        ui_message_id,
        "🔮 Анализ завершён.\n\n"
        "Сейчас я аккуратно собираю выводы,\n"
        "сопоставляю влияния и формирую рекомендации.\n\n"
        "Пожалуйста, подождите несколько секунд."
    )

    time.sleep(3)

    edit_message(
        chat_id,
        ui_message_id,
        "✨ Финальные штрихи…\n"
        "Отчёт почти готов."
    )

    time.sleep(2)

    chunks = split_html(sanitize_html(result_text))

    for chunk in chunks:
        send_message(chat_id, chunk)
        time.sleep(0.3)

def split_html(text: str, limit: int = 3500) -> list[str]:
    parts = []
    buffer = ""

    for block in text.split("\n\n"):
        candidate = block if not buffer else buffer + "\n\n" + block

        if len(candidate) <= limit:
            buffer = candidate
        else:
            if buffer:
                parts.append(buffer)
            buffer = block

    if buffer:
        parts.append(buffer)

    return parts

def sanitize_html(text: str) -> str:
    text = text.replace("&", "&amp;")
    text = text.replace("<br/>", "<br>")
    return text