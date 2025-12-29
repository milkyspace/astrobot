# worker/telegram.py
import os
import requests

TOKEN = os.getenv("BOT_TOKEN")
BASE = f"https://api.telegram.org/bot{TOKEN}"

def edit_message(chat_id: int, message_id: int, text: str):
    requests.post(
        f"{BASE}/editMessageText",
        json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        },
        timeout=10,
    )
