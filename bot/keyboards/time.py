from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def time_keyboard(step: int = 30) -> InlineKeyboardMarkup:
    rows = []
    for h in range(0, 24):
        row = []
        for m in (0, step):
            row.append(
                InlineKeyboardButton(
                    text=f"{h:02d}:{m:02d}",
                    callback_data=f"time:{h:02d}:{m:02d}"
                )
            )
        rows.append(row)

    return InlineKeyboardMarkup(inline_keyboard=rows)
