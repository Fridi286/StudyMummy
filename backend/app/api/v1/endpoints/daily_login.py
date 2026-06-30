import datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.db.session import get_async_db
from app.db.models import User, DailyLogin
from app.api.dependencies import get_current_user

router = APIRouter()

class DailyLoginStatus(BaseModel):
    last_login_date: datetime.date | None
    current_streak: int
    can_claim_today: bool
    reward_amount: int

class DailyLoginClaimResponse(BaseModel):
    coins_awarded: int
    new_balance: int
    current_streak: int
    message: str

class DailyLoginHistoryResponse(BaseModel):
    history: list[datetime.date]

@router.get("/status", response_model=DailyLoginStatus)
async def get_login_status(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    
    can_claim = True
    if current_user.last_login_date == today:
        can_claim = False
        
    # Calculate what the reward would be
    # Streak starts at 1 for day 1. If we can claim today, the new streak will be:
    # If last login was yesterday, new streak is current_streak + 1.
    # Otherwise new streak is 1.
    next_streak = 1
    if current_user.last_login_date == today - datetime.timedelta(days=1):
        next_streak = current_user.current_streak + 1
    elif current_user.last_login_date == today:
        next_streak = current_user.current_streak
        
    reward_amount = min(next_streak, 100)
    
    return DailyLoginStatus(
        last_login_date=current_user.last_login_date,
        current_streak=current_user.current_streak,
        can_claim_today=can_claim,
        reward_amount=reward_amount
    )

@router.post("/claim", response_model=DailyLoginClaimResponse)
async def claim_daily_login(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    today = datetime.datetime.now(datetime.timezone.utc).date()
    
    if current_user.last_login_date == today:
        raise HTTPException(status_code=400, detail="Daily login already claimed today.")
        
    # Update streak
    if current_user.last_login_date == today - datetime.timedelta(days=1):
        current_user.current_streak += 1
    else:
        current_user.current_streak = 1
        
    current_user.last_login_date = today
    
    # Calculate reward: 1 for day 1, 2 for day 2... capping at 100
    reward = min(current_user.current_streak, 100)
    
    current_user.coins += reward
    
    # Record history
    import uuid
    login_record = DailyLogin(
        login_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        login_date=today,
        reward_coins=reward,
        streak_count=current_user.current_streak
    )
    
    db.add(current_user)
    db.add(login_record)
    await db.commit()
    await db.refresh(current_user)
    
    return DailyLoginClaimResponse(
        coins_awarded=reward,
        new_balance=current_user.coins,
        current_streak=current_user.current_streak,
        message=f"Claimed {reward} Study Coins!"
    )

@router.get("/history", response_model=DailyLoginHistoryResponse)
async def get_daily_login_history(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    result = await db.execute(
        select(DailyLogin.login_date)
        .where(DailyLogin.user_id == current_user.user_id)
        .order_by(DailyLogin.login_date.asc())
    )
    history = result.scalars().all()
    return DailyLoginHistoryResponse(history=list(history))
