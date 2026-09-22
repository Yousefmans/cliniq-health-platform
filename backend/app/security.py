import os
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

hasher = PasswordHasher()
bearer = HTTPBearer()


def secret():
    value = os.getenv("JWT_SECRET", "")
    if len(value) < 32:
        raise RuntimeError("JWT_SECRET must contain at least 32 characters")
    return value


def hash_password(password: str) -> str:
    return hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return hasher.verify(hashed, password)
    except (VerifyMismatchError, VerificationError):
        return False


def issue_token(user: User) -> str:
    now = datetime.now(timezone.utc)
    minutes = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))
    return jwt.encode({"sub": str(user.id), "role": user.role, "iat": now, "exp": now + timedelta(minutes=minutes)}, secret(), algorithm="HS256")


def current_user(auth: HTTPAuthorizationCredentials = Depends(bearer), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(auth.credentials, secret(), algorithms=["HS256"])
        user = db.get(User, int(payload["sub"]))
    except (jwt.PyJWTError, KeyError, ValueError, TypeError):
        raise HTTPException(401, "Invalid or expired token")
    if not user or not user.is_active or user.role != payload.get("role"):
        raise HTTPException(401, "Invalid or expired token")
    return user


def require_role(*roles):
    def allowed(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return allowed
