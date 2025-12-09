import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

# Routers
from bot.handlers.start import router as start_router
from bot.handlers.menu import router as menu_router
from bot.handlers.payment import router as payment_router

load_dotenv()

async def main():
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

    bot = Bot(token=os.getenv("BOT_TOKEN"))
    dp = Dispatcher(storage=MemoryStorage())

    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(payment_router)

    print("🤖 Bot started...")

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
