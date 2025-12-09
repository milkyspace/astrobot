import re
from typing import Optional

DATE_REGEX = r"^\d{2}\.\d{2}\.\d{4}$"
TIME_REGEX = r"^\d{2}:\d{2}$"


def validate_date(text: str) -> bool:
    """Проверка формата даты."""
    return re.match(DATE_REGEX, text) is not None


def validate_time(text: str) -> bool:
    """Проверка формата времени."""
    return re.match(TIME_REGEX, text) is not None
