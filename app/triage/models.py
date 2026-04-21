from pydantic import BaseModel
from typing import Optional


# ── Requêtes entrantes ────────────────────────────

class TriageRequest(BaseModel):
    appointment_id: str
    symptoms:       str
    duration:       str    # ex: "3 jours"
    severity:       int    # 1 à 10
    medical_history: Optional[str] = None


# ── Réponses sortantes ────────────────────────────

class TriageOut(BaseModel):
    appointment_id: str
    summary:        str
    urgency_level:  str    # "low", "medium", "high"
    recommendations: str