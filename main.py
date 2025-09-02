from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import *
from app.db.init_db import init_db
from app.core.security import get_current_user  
from app.models import User

app = FastAPI(
    title="Gamedev",
    description="GameDev API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # tu frontend en dev (Vite/React)
        "https://gamedev.study",   # dominio frontend en prod
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()

# Rutas públicas
app.include_router(authRouter)  # login, register, oauth

# Rutas protegidas con token
app.include_router(
    gameRouter,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    marblesRouter
)
app.include_router(
    usersRouter,
    dependencies=[Depends(get_current_user)]
)
app.include_router(
    arcadeRouter
)
