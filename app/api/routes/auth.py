from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, insert, or_
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from urllib.parse import urlencode
import httpx

from app.db.session import get_async_session
from app.models import User
from app.schemas.user import UserRegister
from app.schemas.token import Token
from app.core.security import (
    hash_password,
    validate_password,
    verify_password,
    create_access_token,
    get_current_user,
    auth_scheme
)
from app.core.config import settings

authRouter = APIRouter(prefix="/auth", tags=["auth"])


# Obtener usuario actual (restringido con token)
@authRouter.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@authRouter.post("/register")
async def register_user(
    user: UserRegister,
    session: AsyncSession = Depends(get_async_session),
):
    # ✅ Validar contraseña
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
# Login con usuario o email
@authRouter.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
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


# Google OAuth - Iniciar login
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


# Google OAuth - Callback
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
        # Obtener token
        resp = await client.post(token_url, data=params)
        if resp.status_code != 200:
            raise HTTPException(400, "Failed to get access token from Google")
        token_data = resp.json()

        # Obtener datos del usuario
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
<<<<<<< HEAD
            password=hash_password("google_oauth_dummy")
=======
            profile_image=google_user.get("picture"),
            password=hash_password("google_oauth_dummy")  # dummy para cumplir esquema
>>>>>>> 57aff4c9858976b50a27c0d7f8466e634bcb7b43
        )
        session.add(u)
        await session.commit()
        await session.refresh(u)

    # Crear JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": u.username},
        expires_delta=access_token_expires
    )

    redirect_url = f"{settings.FRONTEND_BASE_URL}/auth/google/callback?{urlencode({'token': access_token})}"
    return RedirectResponse(redirect_url)


# GitHub OAuth - Iniciar login
@authRouter.get("/github/login")
async def github_login():
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize"
        f"?client_id={settings.github_client_id}"
        f"&scope=user:email",
        status_code=302
    )


# GitHub OAuth - Callback
@authRouter.get("/github/callback")
async def github_callback(code: str, session: AsyncSession = Depends(get_async_session)):
    async with httpx.AsyncClient() as client:
        # Obtener token
        response = await client.post(
            url="https://github.com/login/oauth/access_token",
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": code,
            },
            headers={"Accept": "application/json"}
        )
        token_data = response.json()
        access_token = token_data.get("access_token")

        # Obtener datos del usuario
        user_response = await client.get(
            url="https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        user_data = user_response.json()
        email = user_data.get("email")

        # Si no hay email, obtenerlo de /user/emails
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

    # Buscar o crear usuario
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

    # Crear JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    jwt_token = create_access_token(
        data={"sub": u.username},
        expires_delta=access_token_expires
    )

    redirect_url = f"{settings.FRONTEND_BASE_URL}/auth/github/callback?{urlencode({'token': jwt_token})}"
    return RedirectResponse(redirect_url)


# Logout (placeholder)
@authRouter.get("/logout")
async def logout_user(current_user: User = Depends(get_current_user)):
    # Aquí puedes invalidar el token si usas una lista negra (blacklist)
    return {"message": "User logged out successfully"}
