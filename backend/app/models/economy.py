from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from app.models.inventory import ItemResponse
from app.api.v1.endpoints.social import UserPublic

class TradeItemBase(BaseModel):
    item_id: str
    quantity: int

class TradeItemCreate(TradeItemBase):
    owner_id: str

class TradeItemResponse(TradeItemBase):
    model_config = ConfigDict(from_attributes=True)

    trade_item_id: str
    trade_id: str
    owner_id: str
    item: ItemResponse

class TradeBase(BaseModel):
    receiver_id: str
    sender_coins: int = 0
    receiver_coins: int = 0

class TradeCreate(TradeBase):
    trade_items: list[TradeItemCreate] = Field(default_factory=list)

class TradeResponse(TradeBase):
    model_config = ConfigDict(from_attributes=True)

    trade_id: str
    sender_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    
    sender: UserPublic
    receiver: UserPublic
    trade_items: list[TradeItemResponse]
