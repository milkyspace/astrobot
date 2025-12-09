from aiogram.fsm.state import StatesGroup, State

class SolarForm(StatesGroup):
    birth_date = State()
    birth_time = State()
    birth_city = State()
    living_city = State()   # город проживания для соляра
    confirm = State()
