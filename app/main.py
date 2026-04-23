import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.auth.router import router as auth_router
from app.appointments.router import router as appointments_router
from app.video.router import router as video_router
from app.payments.router import router as payments_router
from app.triage.router import router as triage_router
from app.records.router import router as records_router

app = FastAPI(
    title="Medivio API",
    version="0.1.0",
    docs_url="/docs",
)

# CORS
origins = [
    "http://localhost:3000",
    "https://medivio-frontend.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modules
app.include_router(auth_router, prefix="/api/v1")
app.include_router(appointments_router, prefix="/api/v1")
app.include_router(video_router, prefix="/api/v1")
app.include_router(payments_router, prefix="/api/v1")
app.include_router(triage_router, prefix="/api/v1")
app.include_router(records_router, prefix="/api/v1")


@app.get("/")
async def health():
    return {"status": "ok", "env": os.environ.get("APP_ENV", "development")}