from pydantic import BaseModel
from datetime import datetime
from app.models.inventory import ItemResponse
from app.api.v1.endpoints.social import UserPublic

class TradeItemBase(BaseModel):
    item_id: str
    quantity: int

class TradeItemCreate(TradeItemBase):
    owner_id: str

class TradeItemResponse(TradeItemBase):
    trade_item_id: str
    trade_id: str
    owner_id: str
    item: ItemResponse

    class Config:
        from_attributes = True

class TradeBase(BaseModel):
    receiver_id: str
    sender_coins: int = 0
    receiver_coins: int = 0

class TradeCreate(TradeBase):
    trade_items: list[TradeItemCreate] = []

class TradeResponse(TradeBase):
    trade_id: str
    sender_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    sender: UserPublic
    receiver: UserPublic
    trade_items: list[TradeItemResponse]

    class Config:
        from_attributes = True
