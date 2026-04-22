import os
from fastapi import APIRouter, HTTPException, status, Depends
from supabase import create_client, Client
from app.config import settings
from app.auth.models import UserOut, UserRole
from app.auth.dependencies import get_current_user, require_doctor
from app.appointments.models import (
    AppointmentCreate, AppointmentUpdate, AppointmentOut
)

router = APIRouter(prefix="/appointments", tags=["appointments"])

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)


@router.post("/", response_model=AppointmentOut, status_code=201)
async def create_appointment(
    body: AppointmentCreate,
    current_user: UserOut = Depends(get_current_user)
):
    """Patient crée un rendez-vous."""
    try:
        res = supabase.table("appointments").insert({
            "patient_id":   current_user.id,
            "doctor_id":    body.doctor_id,
            "scheduled_at": body.scheduled_at.isoformat(),
            "status":       "pending",
        }).execute()
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    return res.data[0]


@router.get("/", response_model=list[AppointmentOut])
async def list_appointments(
    current_user: UserOut = Depends(get_current_user)
):
    """Liste les rendez-vous selon le rôle."""
    try:
        if current_user.role == UserRole.patient:
            res = supabase.table("appointments")\
                .select("*")\
                .eq("patient_id", current_user.id)\
                .execute()
        else:
            res = supabase.table("appointments")\
                .select("*")\
                .eq("doctor_id", current_user.id)\
                .execute()
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    return res.data


@router.get("/{appointment_id}", response_model=AppointmentOut)
async def get_appointment(
    appointment_id: str,
    current_user: UserOut = Depends(get_current_user)
):
    """Détail d'un rendez-vous."""
    res = supabase.table("appointments")\
        .select("*")\
        .eq("id", appointment_id)\
        .execute()

    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rendez-vous introuvable")

    return res.data[0]


@router.patch("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: str,
    body: AppointmentUpdate,
    current_user: UserOut = Depends(require_doctor)
):
    """Médecin confirme, annule ou complète un rendez-vous."""
    update_data = {"status": body.status.value}
    if body.notes:
        update_data["notes"] = body.notes

    res = supabase.table("appointments")\
        .update(update_data)\
        .eq("id", appointment_id)\
        .execute()

    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rendez-vous introuvable")

    return res.data[0]


@router.delete("/{appointment_id}", status_code=204)
async def cancel_appointment(
    appointment_id: str,
    current_user: UserOut = Depends(get_current_user)
):
    """Patient annule son rendez-vous."""
    supabase.table("appointments")\
        .update({"status": "cancelled"})\
        .eq("id", appointment_id)\
        .eq("patient_id", current_user.id)\
        .execute()
    return
    