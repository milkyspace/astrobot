import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """
    Глобальные настройки проекта, загружаемые из .env
    """

    BOT_TOKEN: str = os.getenv("BOT_TOKEN")

    DATABASE_URL: str = os.getenv("DATABASE_URL")

    REDIS_URL: str = os.getenv("REDIS_URL")

    # цены услуг
    PRICES = {
        "natal": int(os.getenv("PRICE_NATAL", "150")),
        "karma": int(os.getenv("PRICE_KARMA", "150")),
        "solar": int(os.getenv("PRICE_SOLAR", "150")),
    }

    ADMIN_TG_IDS = {
        int(x) for x in os.getenv("ADMIN_TG_IDS", "").split(",") if x
    }

    # YooKassa
    YK_SHOP_ID: str = os.getenv("YOOKASSA_SHOP_ID")
    YK_SECRET_KEY: str = os.getenv("YOOKASSA_SECRET_KEY")

    # задержка расчёта (в секундах)
    MIN_DELAY: int = int(os.getenv("DELAY_MIN", "480"))   # 8 мин
    MAX_DELAY: int = int(os.getenv("DELAY_MAX", "720"))   # 12 мин


settings = Settings()
