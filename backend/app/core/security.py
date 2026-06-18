from datetime import datetime, timedelta, timezone
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import jwt


from typing_extensions import TypedDict
from app.core.config import get_settings

class TokenPayload(TypedDict, total=False):
    sub: str
    username: str
    first_name: str
    last_name: str
    avatar_url: str | None
    exp: datetime
    iat: datetime

settings = get_settings()
ph = PasswordHasher()

def get_password_hash(password: str) -> str:
    return ph.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False

def create_access_token(data: TokenPayload, expires_delta: timedelta | None = None) -> str:
    to_encode_dict = dict(data)
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=60 * 24)  # Default 24 hours
    to_encode_dict.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    encoded_jwt = jwt.encode(to_encode_dict, settings.secret_key, algorithm="HS256")  # type: ignore
    return encoded_jwt
