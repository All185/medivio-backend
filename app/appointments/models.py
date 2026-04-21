from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class AppointmentStatus(str, Enum):
    pending   = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


# ── Requêtes entrantes ────────────────────────────

class AppointmentCreate(BaseModel):
    doctor_id:    str
    scheduled_at: datetime


class AppointmentUpdate(BaseModel):
    status: AppointmentStatus
    notes:  Optional[str] = None


# ── Réponses sortantes ────────────────────────────

class AppointmentOut(BaseModel):
    id:           str
    patient_id:   str
    doctor_id:    str
    scheduled_at: datetime
    status:       AppointmentStatus
    notes:        Optional[str] = None
    created_at:   datetime
    