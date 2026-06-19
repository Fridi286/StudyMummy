import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_async_db
from app.db.models import User, Item, InventoryItem, ActiveItem
from app.api.dependencies import get_current_user
from app.models.inventory import ItemResponse
from app.models.shop import BuyRequest, BuyResponse

router = APIRouter()

@router.get("/items", response_model=list[ItemResponse])
async def get_shop_items(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Item).where(Item.is_buyable == True)
    result = await db.execute(stmt)
    items = result.scalars().all()
    return items

@router.post("/items/{item_id}/buy", response_model=BuyResponse)
async def buy_item(
    item_id: str,
    buy_request: BuyRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    if buy_request.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be greater than 0")

    # Fetch item
    stmt = select(Item).where(Item.item_id == item_id)
    result = await db.execute(stmt)
    item = result.scalars().first()

    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if not item.is_buyable:
        raise HTTPException(status_code=400, detail="Item is not buyable")

    total_cost = item.cost * buy_request.quantity

    if current_user.coins < total_cost:
        raise HTTPException(status_code=400, detail="Insufficient coins")

    # Deduct coins
    current_user.coins -= total_cost

    # Upsert inventory item
    stmt_inv = select(InventoryItem).where(
        (InventoryItem.user_id == current_user.user_id) &
        (InventoryItem.item_id == item_id)
    )
    result_inv = await db.execute(stmt_inv)
    inv_item = result_inv.scalars().first()
    
    # Check if already active/equipped
    stmt_act = select(ActiveItem).where(
        (ActiveItem.user_id == current_user.user_id) &
        (ActiveItem.item_id == item_id)
    )
    result_act = await db.execute(stmt_act)
    act_item = result_act.scalars().first()

    if item.type.lower() == "cosmetic":
        if buy_request.quantity > 1:
            raise HTTPException(status_code=400, detail="Cannot buy more than 1 cosmetic at a time")
        if inv_item or act_item:
            raise HTTPException(status_code=400, detail="You already own this cosmetic")

    if inv_item:
        inv_item.quantity += buy_request.quantity
    else:
        inv_item = InventoryItem(
            inventory_id=str(uuid.uuid4()),
            user_id=current_user.user_id,
            item_id=item_id,
            quantity=buy_request.quantity
        )
        db.add(inv_item)

    await db.commit()

    return BuyResponse(
        message=f"Successfully purchased {buy_request.quantity}x {item.name}.",
        new_coin_balance=current_user.coins
    )
