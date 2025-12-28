import asyncio
import os
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.client.default import DefaultBotProperties

from bot.handlers.start import router as start_router
from bot.handlers.menu import router as menu_router
from bot.handlers.natal import router as natal_router
from bot.handlers.karma import router as karma_router
from bot.handlers.solar import router as solar_router


async def main():
    logging.basicConfig(level=logging.INFO)

    # подключение к Redis для FSM
    storage = RedisStorage.from_url(os.getenv("REDIS_URL"))

    bot = Bot(
        token=os.getenv("BOT_TOKEN"),
        default=DefaultBotProperties(parse_mode="HTML")
    )

    dp = Dispatcher(storage=storage)

    # регистрируем хендлеры
    dp.include_router(start_router)
    dp.include_router(menu_router)
    dp.include_router(natal_router)
    dp.include_router(karma_router)
    dp.include_router(solar_router)

    print("🤖 Bot started...")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
