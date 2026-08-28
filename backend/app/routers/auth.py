from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import CurrentUser
from app.schemas.auth import AuthUserResponse, LoginRequest, LoginResponse
from app.services.auth_service import authenticate_user, issue_login_response

router = APIRouter(prefix="/auth", tags=["Auth"])
DbSession = Annotated[Session, Depends(get_db)]


@router.post("/login", response_model=LoginResponse, summary="로그인")
def login(payload: LoginRequest, db: DbSession) -> dict[str, object]:
    user = authenticate_user(db, payload.username, payload.password)
    return issue_login_response(user)


@router.get("/me", response_model=AuthUserResponse, summary="현재 로그인 사용자")
def me(user: CurrentUser) -> dict[str, str]:
    return {"username": user.username, "role": user.role}
