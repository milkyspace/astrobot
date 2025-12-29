import requests
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
BASE = f"https://api.telegram.org/bot{BOT_TOKEN}"


def edit_message(chat_id: int, message_id: int, text: str):
    requests.post(
        f"{BASE}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )

def send_message(chat_id: int, text: str):
    requests.post(
        f"{BASE}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )