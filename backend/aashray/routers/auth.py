from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from aashray.database import get_db
from aashray.models import User
from aashray.schemas import LoginRequest, TokenResponse
from aashray.security import create_access_token, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == body.email))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    token = create_access_token(user_id=user.id, role=user.role)
    return TokenResponse(
        access_token=token,
        role=user.role,  # type: ignore[arg-type]
        user_id=user.id,
        email=user.email,
    )
