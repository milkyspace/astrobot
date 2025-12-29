from pydantic import BaseModel
from typing import Optional, Dict

class UserDTO(BaseModel):
    id: int
    tg_id: int
    first_name: Optional[str]
    last_name: Optional[str]


class OrderItemDTO(BaseModel):
    birth_date: str
    birth_time: str
    birth_city: str
    extra_data: Dict = {}


class OrderDTO(BaseModel):
    id: int
    tg_id: int
    type: str
    status: str
    result: Optional[str]


from datetime import datetime
class PaymentDTO(BaseModel):
    id: int
    order_id: int
    yookassa_id: str
    amount: int
    status: str
    url: str
    created_at: datetime
