# app/api/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException
import httpx
from sqlalchemy import select, insert, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import User
from app.schemas.user import UserRegister, UserLogin
from app.db.session import get_async_session
from app.core.security import hash_password, verify_password
from app.core.security import create_access_token, auth_scheme
from app.schemas.token import Token
from app.core.config import settings
from datetime import timedelta
from app.core.security import get_current_user
from app.models import User

authRouter = APIRouter(prefix="/auth", tags=["auth"])

@authRouter.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@authRouter.post("/register")
async def register_user(
    user: UserRegister,
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(User).where(User.email == user.email)
    result = await session.execute(stmt)            
    u = result.scalars().first()

    if u:
        raise HTTPException(400, "Email already registered")

    hashed_password = hash_password(user.password)
    new_user = User(
        username=user.username,
        fullname=user.fullname,
        email=user.email,
        password=hashed_password
    )
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return {"message": "User registered successfully", "user": new_user}
from fastapi.security import OAuth2PasswordRequestForm

@authRouter.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),  # ← aquí depende del formulario oauth2
    session: AsyncSession = Depends(get_async_session)
):
    identifier = form_data.username
    password = form_data.password

    stmt = select(User).where(
        or_(
            User.email == identifier,
            User.username == identifier
        )
    )
    result = await session.execute(stmt)
    u = result.scalars().first()

    if not u or not verify_password(password, u.password):
        raise HTTPException(400, "Invalid username/email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": u.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@authRouter.get("/all")
async def get_all_users(session: AsyncSession = Depends(get_async_session)):
    users_query = select(User)
    result = await session.execute(users_query)
    users = result.scalars().all()
    return users
@authRouter.get("/google/callback")
async def google_callback(code: str, session: AsyncSession = Depends(get_async_session)):
    token_url = "https://oauth2.googleapis.com/token"
    params = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data=params)
        if resp.status_code != 200:
            raise HTTPException(400, "Failed to get access token from Google")
        token_data = resp.json()

        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        userinfo_resp = await client.get(userinfo_url, headers=headers)
        if userinfo_resp.status_code != 200:
            raise HTTPException(400, "Failed to fetch user info from Google")
        google_user = userinfo_resp.json()

    # Buscar o crear usuario
    stmt = select(User).where(User.email == google_user["email"])
    result = await session.execute(stmt)
    u = result.scalars().first()

    if not u:
        u = User(
            username=google_user["email"].split("@")[0],
            fullname=google_user.get("name", ""),
            email=google_user["email"],
            password=hash_password("google_oauth_dummy")  # dummy para cumplir esquema
        )
        session.add(u)
        await session.commit()
        await session.refresh(u)

    # Crear token JWT para tu API
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": u.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}
from fastapi.responses import RedirectResponse
from urllib.parse import urlencode

@authRouter.get("/google/login")
async def google_login():
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    return RedirectResponse(url)
