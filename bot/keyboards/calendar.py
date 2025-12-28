from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import date
import calendar


def calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    cal = calendar.Calendar()
    rows = []

    rows.append([
        InlineKeyboardButton(text="◀️", callback_data=f"cal:prev:{year}:{month}"),
        InlineKeyboardButton(text=f"{calendar.month_name[month]} {year}", callback_data="noop"),
        InlineKeyboardButton(text="▶️", callback_data=f"cal:next:{year}:{month}"),
    ])

    week = []
    for d in cal.itermonthdays(year, month):
        if d == 0:
            week.append(InlineKeyboardButton(text=" ", callback_data="noop"))
        else:
            week.append(
                InlineKeyboardButton(
                    text=str(d),
                    callback_data=f"cal:day:{year}:{month}:{d}"
                )
            )
        if len(week) == 7:
            rows.append(week)
            week = []

    return InlineKeyboardMarkup(inline_keyboard=rows)
