import os
import asyncio
from aiogram import Bot
from typing import Optional

bot = Bot(token=os.getenv("BOT_TOKEN"))

_loop: Optional[asyncio.AbstractEventLoop] = None

def run_async(coro):
    global _loop

    if _loop is None or _loop.is_closed():
        _loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_loop)

    return _loop.run_until_complete(coro)

def send_message(chat_id: int, text: str):
    run_async(bot.send_message(chat_id, text))
