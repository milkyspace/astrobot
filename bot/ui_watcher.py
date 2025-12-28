import asyncio
from aiogram import Bot
from bot.services.db import Db
from bot.services.order_service import OrderService


async def order_ui_watcher(bot: Bot):
    db = Db()
    orders = OrderService(db)

    while True:
        pending = orders.get_orders_with_pending_ui()

        for order in pending:
            try:
                await bot.edit_message_text(
                    chat_id=order["chat_id"],
                    message_id=order["ui_message_id"],
                    text=order["ui_text"],
                )
            except Exception:
                pass

        await asyncio.sleep(2)
