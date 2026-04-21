from pydantic import BaseModel
from typing import Optional


# ── Requêtes entrantes ────────────────────────────

class RoomCreate(BaseModel):
    appointment_id: str


# ── Réponses sortantes ────────────────────────────

class RoomOut(BaseModel):
    room_name:  str
    room_url:   str
    token:      str
    expires_at: Optional[int] = None