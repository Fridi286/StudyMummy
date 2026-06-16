import uuid
from typing import Annotated, ClassVar
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, ConfigDict
from fastapi.security import OAuth2PasswordRequestForm

from app.db.session import get_async_db
from app.db.models import User
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()

class UserCreate(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    user_id: str
    username: str
    email: EmailStr
    coins: int

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

class SessionCreate(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str


@router.post("/user", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: Annotated[AsyncSession, Depends(get_async_db)]) -> User:
    # Check if user with email or username exists
    stmt = select(User).where((User.email == user_in.email) | (User.username == user_in.username))
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(
            status_code=400,
            detail="The user with this username or email already exists in the system.",
        )
    
    # Create new user
    user = User(
        user_id=str(uuid.uuid4()),
        username=user_in.username,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        email=user_in.email,
        password_hash=get_password_hash(user_in.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user

@router.post("/session", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], 
    db: Annotated[AsyncSession, Depends(get_async_db)]
) -> Token:
    # OAuth2 spec requires the field to be named "username", but we expect an email address.
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user.user_id})
    return Token(access_token=access_token, token_type="bearer")
