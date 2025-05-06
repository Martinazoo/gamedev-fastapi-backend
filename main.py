from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import authRouter
from app.db.init_db import init_db

app = FastAPI(
    title="Mi Proyecto FastAPI",
    description="API de ejemplo con estructura modular",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def on_startup():
    await init_db()
    
app.include_router(authRouter)