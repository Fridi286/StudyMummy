from pydantic import BaseModel
from app.models.inventory import ItemResponse

class BuyRequest(BaseModel):
    quantity: int = 1

class BuyResponse(BaseModel):
    message: str
    new_coin_balance: int
