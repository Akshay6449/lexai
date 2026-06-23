"""
Auth routes: login, token refresh, logout, me.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from auth.jwt_handler import (
    verify_password, create_access_token, create_refresh_token,
    decode_token, get_current_user
)
from core.database import AsyncSession, get_db, User, AuditLog

router = APIRouter()


# ── Schemas ──────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str
    last_login: str | None


# ── Routes ───────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    user = (
        await db.execute(select(User).where(User.email == payload.email))
    ).scalar_one_or_none()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials.")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated.")

    # Update last login
    user.last_login = datetime.now(timezone.utc)

    # Audit
    db.add(AuditLog(
        user_id=user.id,
        action="USER_LOGIN",
        details=f"Login from {request.client.host}",
        ip_address=request.client.host,
    ))
    await db.commit()

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role, user.email),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    data = decode_token(payload.refresh_token)
    if data.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Not a refresh token.")

    user = (
        await db.execute(select(User).where(User.id == data["sub"]))
    ).scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found.")

    return TokenResponse(
        access_token=create_access_token(str(user.id), user.role, user.email),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.get("/me", response_model=MeResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return MeResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        last_login=current_user.last_login.isoformat() if current_user.last_login else None,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # In production: add token JTI to a blocklist in Redis
    db.add(AuditLog(
        user_id=current_user.id,
        action="USER_LOGOUT",
        details="User logged out",
    ))
    await db.commit()
    return {"message": "Logged out successfully."}
