from aiogram.fsm.state import StatesGroup, State

class NatalForm(StatesGroup):
    birth_date = State()
    birth_time = State()
    birth_city = State()
    confirm = State()
