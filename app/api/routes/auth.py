from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from urllib.parse import urlencode
import httpx

from app.db.session import get_async_session
from app.models import User
from app.schemas.user import UserRegister
from app.core.security import (
    hash_password,
    validate_password,
    verify_password,
    create_access_token,
    get_current_user,
)
from app.core.config import settings

authRouter = APIRouter(prefix="/auth", tags=["auth"])


# -----------------------
# Helper para cookies
# -----------------------
def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=settings.ENV == "production",   # Secure solo en prod (HTTPS)
        samesite="none",                       # permite cross-site
        domain=".gamedev.study" if settings.ENV == "production" else None,  # válido en subdominios
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


# -----------------------
# Endpoints
# -----------------------

# Obtener usuario actual
@authRouter.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


@authRouter.post("/register")
async def register_user(
    user: UserRegister,
    session: AsyncSession = Depends(get_async_session),
):
    validate_password(user.password)

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


@authRouter.post("/login")
async def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_async_session)
):
    identifier = form_data.username
    password = form_data.password

    stmt = select(User).where(or_(User.email == identifier, User.username == identifier))
    result = await session.execute(stmt)
    u = result.scalars().first()

    if not u or not verify_password(password, u.password):
        raise HTTPException(400, "Invalid username/email or password")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": u.username}, expires_delta=access_token_expires
    )

    set_auth_cookie(response, access_token)

    return {"message": "Login successful"}


# -----------------------
# Google OAuth
# -----------------------
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


@authRouter.get("/google/callback")
async def google_callback(
    code: str,
    response: Response,
    session: AsyncSession = Depends(get_async_session)
):
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

    stmt = select(User).where(User.email == google_user["email"])
    result = await session.execute(stmt)
    u = result.scalars().first()
    if not u:
        u = User(
            username=google_user["email"].split("@")[0],
            fullname=google_user.get("name", ""),
            email=google_user["email"],
            password=hash_password("google_oauth_dummy")
        )
        session.add(u)
        await session.commit()
        await session.refresh(u)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": u.username}, expires_delta=access_token_expires
    )

    set_auth_cookie(response, access_token)

    return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/auth/success")


# -----------------------
# GitHub OAuth
# -----------------------
@authRouter.get("/github/login")
async def github_login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&scope=user:email",
        status_code=302
    )


@authRouter.get("/github/callback")
async def github_callback(
    code: str,
    response: Response,
    session: AsyncSession = Depends(get_async_session)
):
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url="https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"}
        )
        token_data = resp.json()
        access_token = token_data.get("access_token")

        user_response = await client.get(
            url="https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        user_data = user_response.json()
        email = user_data.get("email")

        if not email:
            email_response = await client.get(
                url="https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json"
                }
            )
            email_data = email_response.json()
            primary_email = next(
                (item["email"] for item in email_data if item.get("primary") and item.get("verified")),
                None
            )
            if not primary_email:
                raise HTTPException(400, "No se pudo obtener un email válido del usuario de GitHub.")
            email = primary_email

    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    u = result.scalars().first()
    if not u:
        u = User(
            username=email.split("@")[0],
            fullname=user_data.get("name") or "",
            email=email,
            profile_image=user_data.get("avatar_url"),
            password=hash_password("github_oauth_dummy")
        )
        session.add(u)
        await session.commit()
        await session.refresh(u)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = create_access_token(
        data={"sub": u.username}, expires_delta=access_token_expires
    )

    set_auth_cookie(response, jwt_token)

    return RedirectResponse(f"{settings.FRONTEND_BASE_URL}/auth/success")


# -----------------------
# Logout
# -----------------------
@authRouter.post("/logout")
async def logout_user(response: Response):
    response.delete_cookie(
        "access_token",
        domain=".gamedev.study" if settings.ENV == "production" else None
    )
    return {"message": "User logged out successfully"}
