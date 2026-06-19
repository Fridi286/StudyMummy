from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload
import uuid

from app.db.session import get_async_db
from app.db.models import User, Trade, TradeItem, InventoryItem
from app.api.v1.endpoints.auth import get_current_user
from app.models.economy import TradeCreate, TradeResponse

router = APIRouter()
from app.websockets.manager import manager

@router.post("/trades", response_model=TradeResponse)
async def create_trade(
    trade_req: TradeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    if current_user.user_id == trade_req.receiver_id:
        raise HTTPException(status_code=400, detail="Cannot trade with yourself")

    # Verify receiver exists
    receiver = await db.scalar(select(User).where(User.user_id == trade_req.receiver_id))
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Verify sender has enough coins
    if trade_req.sender_coins > current_user.coins:
        raise HTTPException(status_code=400, detail="Not enough coins to offer")

    # Create Trade
    trade_id = str(uuid.uuid4())
    new_trade = Trade(
        trade_id=trade_id,
        sender_id=current_user.user_id,
        receiver_id=trade_req.receiver_id,
        sender_coins=trade_req.sender_coins,
        receiver_coins=trade_req.receiver_coins,
        status="pending"
    )
    db.add(new_trade)

    # Verify and add trade items
    for item_req in trade_req.trade_items:
        if item_req.owner_id not in [current_user.user_id, trade_req.receiver_id]:
            raise HTTPException(status_code=400, detail="Item owner must be sender or receiver")
        
        # Verify sender actually owns the item they are offering
        if item_req.owner_id == current_user.user_id:
            inv_stmt = select(InventoryItem).where(
                InventoryItem.user_id == current_user.user_id,
                InventoryItem.item_id == item_req.item_id
            )
            inv_item = await db.scalar(inv_stmt)
            if not inv_item or inv_item.quantity < item_req.quantity:
                raise HTTPException(status_code=400, detail=f"You do not have enough of item {item_req.item_id}")

        new_item = TradeItem(
            trade_item_id=str(uuid.uuid4()),
            trade_id=trade_id,
            owner_id=item_req.owner_id,
            item_id=item_req.item_id,
            quantity=item_req.quantity
        )
        db.add(new_item)

    await db.commit()
    
    # Notify receiver via WS
    await manager.send_personal_message(trade_req.receiver_id, {"type": "TRADE_UPDATE"})
    
    # Reload with relationships
    stmt = select(Trade).options(
        selectinload(Trade.sender),
        selectinload(Trade.receiver),
        selectinload(Trade.trade_items).selectinload(TradeItem.item)
    ).where(Trade.trade_id == trade_id)
    
    return await db.scalar(stmt)


@router.get("/trades/pending", response_model=list[TradeResponse])
async def get_pending_trades(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Trade).options(
        selectinload(Trade.sender),
        selectinload(Trade.receiver),
        selectinload(Trade.trade_items).selectinload(TradeItem.item)
    ).where(
        and_(
            or_(Trade.sender_id == current_user.user_id, Trade.receiver_id == current_user.user_id),
            Trade.status == "pending"
        )
    )
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/trades/{trade_id}/accept", response_model=TradeResponse)
async def accept_trade(
    trade_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Trade).options(
        selectinload(Trade.sender),
        selectinload(Trade.receiver),
        selectinload(Trade.trade_items)
    ).where(Trade.trade_id == trade_id)
    trade = await db.scalar(stmt)

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    if trade.status != "pending":
        raise HTTPException(status_code=400, detail=f"Trade is already {trade.status}")

    if trade.receiver_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only the receiver can accept the trade")

    # Refresh users to get latest balances
    sender = await db.scalar(select(User).where(User.user_id == trade.sender_id))
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")
    receiver = current_user

    # Verify coin balances
    if sender.coins < trade.sender_coins:
        raise HTTPException(status_code=400, detail="Sender no longer has enough coins")
    if receiver.coins < trade.receiver_coins:
        raise HTTPException(status_code=400, detail="You do not have enough coins")

    # Verify item balances
    for t_item in trade.trade_items:
        inv_stmt = select(InventoryItem).where(
            InventoryItem.user_id == t_item.owner_id,
            InventoryItem.item_id == t_item.item_id
        )
        inv_item = await db.scalar(inv_stmt)
        if not inv_item or inv_item.quantity < t_item.quantity:
            raise HTTPException(status_code=400, detail=f"User {t_item.owner_id} no longer has enough of item {t_item.item_id}")

    # Transfer coins
    sender.coins -= trade.sender_coins
    sender.coins += trade.receiver_coins
    receiver.coins -= trade.receiver_coins
    receiver.coins += trade.sender_coins

    # Transfer items
    for t_item in trade.trade_items:
        # Deduct from owner
        inv_stmt = select(InventoryItem).where(
            InventoryItem.user_id == t_item.owner_id,
            InventoryItem.item_id == t_item.item_id
        )
        inv_item = await db.scalar(inv_stmt)
        if not inv_item:
            raise HTTPException(status_code=500, detail="Inventory item missing during transfer")
        inv_item.quantity -= t_item.quantity
        if inv_item.quantity == 0:
            await db.delete(inv_item)
            
        # Give to other party
        new_owner_id = trade.receiver_id if t_item.owner_id == trade.sender_id else trade.sender_id
        new_inv_stmt = select(InventoryItem).where(
            InventoryItem.user_id == new_owner_id,
            InventoryItem.item_id == t_item.item_id
        )
        new_inv_item = await db.scalar(new_inv_stmt)
        if new_inv_item:
            new_inv_item.quantity += t_item.quantity
        else:
            new_inv = InventoryItem(
                inventory_id=str(uuid.uuid4()),
                user_id=new_owner_id,
                item_id=t_item.item_id,
                quantity=t_item.quantity
            )
            db.add(new_inv)

    trade.status = "accepted"
    await db.commit()
    
    # Notify sender via WS
    await manager.send_personal_message(trade.sender_id, {"type": "TRADE_UPDATE"})
    
    # Reload for response
    reload_stmt = select(Trade).options(
        selectinload(Trade.sender),
        selectinload(Trade.receiver),
        selectinload(Trade.trade_items).selectinload(TradeItem.item)
    ).where(Trade.trade_id == trade_id)
    return await db.scalar(reload_stmt)


@router.post("/trades/{trade_id}/reject", response_model=TradeResponse)
async def reject_trade(
    trade_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Trade).options(
        selectinload(Trade.sender),
        selectinload(Trade.receiver),
        selectinload(Trade.trade_items).selectinload(TradeItem.item)
    ).where(Trade.trade_id == trade_id)
    trade = await db.scalar(stmt)

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
        
    if trade.receiver_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only the receiver can reject the trade")
        
    if trade.status != "pending":
        raise HTTPException(status_code=400, detail=f"Trade is already {trade.status}")

    trade.status = "rejected"
    await db.commit()
    
    # Notify sender via WS
    await manager.send_personal_message(trade.sender_id, {"type": "TRADE_UPDATE"})
    return trade


@router.post("/trades/{trade_id}/cancel", response_model=TradeResponse)
async def cancel_trade(
    trade_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Trade).options(
        selectinload(Trade.sender),
        selectinload(Trade.receiver),
        selectinload(Trade.trade_items).selectinload(TradeItem.item)
    ).where(Trade.trade_id == trade_id)
    trade = await db.scalar(stmt)

    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
        
    if trade.sender_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Only the sender can cancel the trade")
        
    if trade.status != "pending":
        raise HTTPException(status_code=400, detail=f"Trade is already {trade.status}")

    trade.status = "cancelled"
    await db.commit()
    
    # Notify receiver via WS
    await manager.send_personal_message(trade.receiver_id, {"type": "TRADE_UPDATE"})
    return trade
