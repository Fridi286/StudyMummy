import uuid
import io
import os
import datetime
from typing import Annotated, ClassVar
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from fastapi.security import OAuth2PasswordRequestForm
from PIL import Image

from app.db.session import get_async_db
from app.db.models import User
from app.core.security import get_password_hash, verify_password, create_access_token
from app.api.dependencies import get_current_user

router = APIRouter()

class UserCreate(BaseModel):
    username: str = Field(min_length=3)
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=8)

class UserResponse(BaseModel):
    user_id: str
    username: str
    first_name: str
    last_name: str
    email: EmailStr
    coins: int
    experience: int
    level: int
    avatar_url: str | None = None
    last_login_date: datetime.date | None = None
    current_streak: int = 0

    model_config: ClassVar[ConfigDict] = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3)
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8)

class UserUpdateResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"

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
    # OAuth2 spec requires the field to be named "username", and we expect the actual username.
    stmt = select(User).where(User.username == form_data.username)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    access_token = create_access_token(data={
        "sub": user.user_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "avatar_url": user.avatar_url
    })
    return Token(access_token=access_token, token_type="bearer")

@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user_profile(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
) -> User:
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # In the future, we can add logic here to filter private fields if current_user.user_id != user.user_id
    return user

@router.patch("/user/{user_id}", response_model=UserUpdateResponse)
async def update_user_profile(
    user_id: str,
    user_in: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
        
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check for username or email conflicts if they are being updated
    if user_in.username or user_in.email:
        conflict_stmt = select(User).where(
            (User.user_id != user_id) & 
            ((User.email == user_in.email) | (User.username == user_in.username))
        )
        conflict_result = await db.execute(conflict_stmt)
        if conflict_result.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="The username or email is already taken by another user."
            )
        
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["password_hash"] = get_password_hash(update_data.pop("password"))
        
    for field, value in update_data.items():
        setattr(user, field, value)
        
    await db.commit()
    await db.refresh(user)
    
    access_token = create_access_token(data={
        "sub": user.user_id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "avatar_url": user.avatar_url
    })
    
    return UserUpdateResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        token_type="bearer"
    )

@router.post("/user/{user_id}/avatar", response_model=UserUpdateResponse)
async def upload_user_avatar(
    user_id: str,
    file: UploadFile,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to update this profile")
        
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Crop to square
        width, height = image.size
        size = min(width, height)
        left = (width - size) / 2
        top = (height - size) / 2
        right = (width + size) / 2
        bottom = (height + size) / 2
        
        image = image.crop((left, top, right, bottom))
        
        # Resize
        image = image.resize((256, 256), Image.Resampling.LANCZOS)
        
        # Convert RGBA to RGB if saving as WebP without alpha, though WebP supports alpha.
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
            
        # Save as webp
        file_path = f"static/avatars/{user_id}.webp"
        image.save(file_path, "WEBP", quality=85)
        
        # Update user
        user.avatar_url = f"/{file_path}"
        await db.commit()
        await db.refresh(user)
        
        # Generate new token
        access_token = create_access_token(data={
            "sub": user.user_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "avatar_url": user.avatar_url
        })
        
        return UserUpdateResponse(
            user=UserResponse.model_validate(user),
            access_token=access_token,
            token_type="bearer"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image file: {str(e)}")
