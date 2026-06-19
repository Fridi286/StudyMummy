import uuid
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.db.session import get_async_db
from app.db.models import User, InventoryItem, ActiveItem, Item
from app.api.dependencies import get_current_user
from app.models.inventory import (
    UserInventoryResponse,
    UseItemResponse,
    InventoryItemResponse,
    ActiveItemResponse
)

router = APIRouter()

@router.get("/", response_model=UserInventoryResponse)
async def get_inventory(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    # Fetch inventory items
    stmt_inv = select(InventoryItem).options(joinedload(InventoryItem.item)).where(
        (InventoryItem.user_id == current_user.user_id) &
        (InventoryItem.quantity > 0)
    )
    result_inv = await db.execute(stmt_inv)
    inventory_items = result_inv.scalars().all()

    # Fetch active items that haven't expired, or are permanent (expires_at is null)
    now = datetime.now(timezone.utc)
    stmt_active = select(ActiveItem).options(joinedload(ActiveItem.item)).where(
        (ActiveItem.user_id == current_user.user_id) &
        ((ActiveItem.expires_at > now) | (ActiveItem.expires_at.is_(None)))
    )
    result_active = await db.execute(stmt_active)
    active_items = result_active.scalars().all()

    return UserInventoryResponse(
        inventory=[InventoryItemResponse.model_validate(item) for item in inventory_items],
        active_items=[ActiveItemResponse.model_validate(act) for act in active_items]
    )

@router.get("/user/{target_user_id}", response_model=UserInventoryResponse)
async def get_user_inventory(
    target_user_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    # Fetch inventory items
    stmt_inv = select(InventoryItem).options(joinedload(InventoryItem.item)).where(
        (InventoryItem.user_id == target_user_id) &
        (InventoryItem.quantity > 0)
    )
    result_inv = await db.execute(stmt_inv)
    inventory_items = result_inv.scalars().all()

    # Fetch active items
    now = datetime.now(timezone.utc)
    stmt_active = select(ActiveItem).options(joinedload(ActiveItem.item)).where(
        (ActiveItem.user_id == target_user_id) &
        ((ActiveItem.expires_at > now) | (ActiveItem.expires_at.is_(None)))
    )
    result_active = await db.execute(stmt_active)
    active_items = result_active.scalars().all()

    return UserInventoryResponse(
        inventory=[InventoryItemResponse.model_validate(item) for item in inventory_items],
        active_items=[ActiveItemResponse.model_validate(act) for act in active_items]
    )

@router.post("/items/{item_id}/use", response_model=UseItemResponse)
async def use_item(
    item_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    # Fetch the inventory item
    stmt = select(InventoryItem).options(joinedload(InventoryItem.item)).where(
        (InventoryItem.user_id == current_user.user_id) &
        (InventoryItem.item_id == item_id)
    )
    result = await db.execute(stmt)
    inv_item = result.scalars().first()

    if not inv_item or inv_item.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You do not own this item or it is out of stock."
        )

    item = inv_item.item
    effects = item.effects or {}
    
    # 1. Decrease quantity
    inv_item.quantity -= 1

    instant_effects_applied = {}
    active_item = None

    # 2. Handle Instant Effects
    if "instant_xp" in effects:
        instant_xp = int(effects["instant_xp"])
        current_user.experience += instant_xp
        instant_effects_applied["xp_gained"] = instant_xp
        
    if "instant_coins" in effects:
        instant_coins = int(effects["instant_coins"])
        current_user.coins += instant_coins
        instant_effects_applied["coins_gained"] = instant_coins

    # 3. Handle Time-based Buffs or Permanent Cosmetics
    is_cosmetic = item.type.lower() == "cosmetic"
    
    if "duration_minutes" in effects or is_cosmetic:
        now = datetime.now(timezone.utc)
        
        expires_at = None
        if not is_cosmetic and "duration_minutes" in effects:
            duration = int(effects["duration_minutes"])
            if duration > 0:
                expires_at = now + timedelta(minutes=duration)
        
        # Check if user already has this buff active to extend it, or just create a new one.
        # We will create a new one to keep it simple, or overwrite. Let's create a new one.
        active_item = ActiveItem(
            active_item_id=str(uuid.uuid4()),
            user_id=current_user.user_id,
            item_id=item.item_id,
            name=item.name,
            effects=effects,
            activated_at=now,
            expires_at=expires_at
        )
        db.add(active_item)

    # Commit changes
    await db.commit()
    await db.refresh(inv_item)
    if active_item:
        await db.refresh(active_item)

    return UseItemResponse(
        message=f"Successfully used {item.name}.",
        inventory_item=InventoryItemResponse.model_validate(inv_item),
        active_item=ActiveItemResponse.model_validate(active_item) if active_item else None,
        instant_effects_applied=instant_effects_applied if instant_effects_applied else None
    )

@router.post("/active-items/{active_item_id}/unequip", response_model=dict[str, str])
async def unequip_item(
    active_item_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    # Fetch the active item
    stmt = select(ActiveItem).options(joinedload(ActiveItem.item)).where(
        (ActiveItem.user_id == current_user.user_id) &
        (ActiveItem.active_item_id == active_item_id)
    )
    result = await db.execute(stmt)
    active_item = result.scalars().first()

    if not active_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active item not found."
        )
        
    if active_item.item.type.lower() != "cosmetic":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only cosmetics can be unequipped."
        )
        
    # Return to inventory
    stmt_inv = select(InventoryItem).where(
        (InventoryItem.user_id == current_user.user_id) &
        (InventoryItem.item_id == active_item.item_id)
    )
    result_inv = await db.execute(stmt_inv)
    inv_item = result_inv.scalars().first()
    
    if inv_item:
        inv_item.quantity += 1
    else:
        inv_item = InventoryItem(
            inventory_id=str(uuid.uuid4()),
            user_id=current_user.user_id,
            item_id=active_item.item_id,
            quantity=1
        )
        db.add(inv_item)
        
    # Delete active item
    await db.delete(active_item)
    await db.commit()
    
    return {"message": f"Successfully unequipped {active_item.name}."}
