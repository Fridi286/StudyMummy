import uuid
import random
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_db
from app.db.models import User, SlotMachineLog
from app.api.dependencies import get_current_user
from app.models.gambling import SlotMachineRequest, SlotMachineResponse

router = APIRouter()

# 5 symbols (0 to 4)
NUM_SYMBOLS = 5

@router.post("/slotmachine", response_model=SlotMachineResponse)
async def play_slotmachine(
    request: SlotMachineRequest,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    if request.bet_amount <= 0:
        raise HTTPException(status_code=400, detail="Bet amount must be greater than 0.")
        
    if current_user.coins < request.bet_amount:
        raise HTTPException(status_code=400, detail="Insufficient coins.")
        
    # Deduct bet
    current_user.coins -= request.bet_amount
    
    # Probabilities (negative EV = 0.88)
    # Jackpot (4% chance): 10x
    # Small win (48% chance): 1x
    # Loss (48% chance): 0
    roll = random.random()
    payout = 0
    result = "loss"
    message = "You lost!"
    
    if roll < 0.04:
        payout = request.bet_amount * 10
        result = "jackpot"
        message = "JACKPOT! 3 of a kind!"
    elif roll < 0.52:
        payout = request.bet_amount * 1
        result = "small_win"
        message = "Small win! 2 of a kind."
        
    current_user.coins += payout
    net_change = payout - request.bet_amount
    
    # Log
    log = SlotMachineLog(
        log_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        bet_amount=request.bet_amount,
        payout=payout
    )
    db.add(log)
    
    await db.commit()
    
    return SlotMachineResponse(
        result=result,
        payout=payout,
        net_change=net_change,
        new_balance=current_user.coins,
        message=message
    )
