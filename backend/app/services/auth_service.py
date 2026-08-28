from sqlalchemy import select
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.user import User
from app.services.jwt_service import create_access_token
from app.services.password_service import verify_password

INVALID_CREDENTIALS = "Invalid username or password"
INACTIVE_ACCOUNT = "This account is inactive"


def authenticate_user(db: Session, username: str, password: str) -> User:
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS,
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=INACTIVE_ACCOUNT,
        )
    return user


def issue_login_response(user: User) -> dict[str, object]:
    return {
        "access_token": create_access_token(username=user.username, role=user.role),
        "token_type": "bearer",
        "user": {"username": user.username, "role": user.role},
    }
