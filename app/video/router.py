from fastapi import APIRouter, HTTPException, status, Depends
from app.config import settings
from app.auth.models import UserOut
from app.auth.dependencies import get_current_user
from app.video.models import RoomCreate, RoomOut
import httpx
from datetime import datetime, timedelta
import os 

router = APIRouter(prefix="/video", tags=["video"])

DAILY_API_URL = "https://api.daily.co/v1"


@router.post("/room", response_model=RoomOut, status_code=201)
async def create_room(
    body: RoomCreate,
    current_user: UserOut = Depends(get_current_user)
):
    """Crée une salle vidéo Daily.co pour un rendez-vous."""
    headers = {
        "Authorization": f"Bearer {settings.DAILY_API_KEY}",
        "Content-Type":  "application/json",
    }

    # Expire dans 2 heures
    expires_at = int((datetime.utcnow() + timedelta(hours=2)).timestamp())

    room_payload = {
        "name":       f"appointment-{body.appointment_id}",
        "properties": {
            "exp":        expires_at,
            "max_participants": 2,
            "enable_chat": True,
        }
    }

    async with httpx.AsyncClient() as client:
        # Créer la salle
        room_res = await client.post(
            f"{DAILY_API_URL}/rooms",
            headers=headers,
            json=room_payload,
        )

        if room_res.status_code != 200:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Erreur création salle Daily.co"
            )

        room = room_res.json()

        # Générer un token pour l'utilisateur
        token_payload = {
            "properties": {
                "room_name": room["name"],
                "exp":       expires_at,
                "is_owner":  True,
            }
        }

        token_res = await client.post(
            f"{DAILY_API_URL}/meeting-tokens",
            headers=headers,
            json=token_payload,
        )

        if token_res.status_code != 200:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Erreur génération token Daily.co"
            )

        token = token_res.json()

    return RoomOut(
        room_name=room["name"],
        room_url=room["url"],
        token=token["token"],
        expires_at=expires_at,
    )


@router.get("/token/{room_name}", response_model=RoomOut)
async def get_room_token(
    room_name: str,
    current_user: UserOut = Depends(get_current_user)
):
    """Génère un token d'accès pour rejoindre une salle existante."""
    headers = {
        "Authorization": f"Bearer {settings.DAILY_API_KEY}",
        "Content-Type":  "application/json",
    }

    expires_at = int((datetime.utcnow() + timedelta(hours=2)).timestamp())

    token_payload = {
        "properties": {
            "room_name": room_name,
            "exp":       expires_at,
            "is_owner":  False,
        }
    }

    async with httpx.AsyncClient() as client:
        token_res = await client.post(
            f"{DAILY_API_URL}/meeting-tokens",
            headers=headers,
            json=token_payload,
        )

        if token_res.status_code != 200:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Erreur génération token Daily.co"
            )

        token = token_res.json()

    return RoomOut(
        room_name=room_name,
        room_url=f"https://api.daily.co/{room_name}",
        token=token["token"],
        expires_at=expires_at,
    )