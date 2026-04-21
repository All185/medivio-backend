from pydantic import BaseModel
from typing import Optional


# ── Requêtes entrantes ────────────────────────────

class CheckoutCreate(BaseModel):
    appointment_id: str
    amount:         int    # en centimes ex: 5000 = 50.00€
    currency:       str = "eur"
    success_url:    str
    cancel_url:     str


# ── Réponses sortantes ────────────────────────────

class CheckoutOut(BaseModel):
    checkout_url:  str
    session_id:    str


class WebhookResponse(BaseModel):
    status:  str
    message: Optional[str] = None