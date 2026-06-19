from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict


class ItemResponse(BaseModel):
    item_id: str
    name: str
    type: str
    icon_url: str | None = None
    effects: dict[str, Any] | None = None
    cost: int

    model_config = ConfigDict(from_attributes=True)


class InventoryItemResponse(BaseModel):
    inventory_id: str
    quantity: int
    acquired_at: datetime
    item: ItemResponse

    model_config = ConfigDict(from_attributes=True)


class ActiveItemResponse(BaseModel):
    active_item_id: str
    item: ItemResponse
    name: str
    effects: dict[str, Any]
    activated_at: datetime
    expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class UserInventoryResponse(BaseModel):
    inventory: list[InventoryItemResponse]
    active_items: list[ActiveItemResponse]


class UseItemResponse(BaseModel):
    message: str
    inventory_item: InventoryItemResponse
    active_item: ActiveItemResponse | None = None
    instant_effects_applied: dict[str, Any] | None = None
