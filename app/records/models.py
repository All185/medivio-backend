from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# ── Requêtes entrantes ────────────────────────────

class RecordCreate(BaseModel):
    appointment_id: str
    patient_id:     str
    diagnosis:      str
    prescription:   Optional[str] = None
    notes:          Optional[str] = None


class RecordUpdate(BaseModel):
    diagnosis:    Optional[str] = None
    prescription: Optional[str] = None
    notes:        Optional[str] = None


# ── Réponses sortantes ────────────────────────────

class RecordOut(BaseModel):
    id:             str
    appointment_id: str
    patient_id:     str
    doctor_id:      str
    diagnosis:      str
    prescription:   Optional[str] = None
    notes:          Optional[str] = None
    created_at:     datetime