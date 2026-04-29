from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.notifications.service import send_appointment_confirmation, send_appointment_reminder

router = APIRouter(prefix="/notifications", tags=["notifications"])

class NotificationRequest(BaseModel):
    patient_email: str
    patient_name: str
    doctor_name: str
    scheduled_at: str
    type: str  # "confirmation" ou "reminder"

@router.post("/send")
async def send_notification(
    request: NotificationRequest,
    current_user=Depends(get_current_user)
):
    if request.type == "confirmation":
        success = send_appointment_confirmation(
            request.patient_email,
            request.patient_name,
            request.doctor_name,
            request.scheduled_at
        )
    elif request.type == "reminder":
        success = send_appointment_reminder(
            request.patient_email,
            request.patient_name,
            request.doctor_name,
            request.scheduled_at
        )
    else:
        raise HTTPException(status_code=400, detail="Type de notification invalide")

    if not success:
        raise HTTPException(status_code=500, detail="Erreur lors de l'envoi")

    return {"message": "Notification envoyée avec succès"}