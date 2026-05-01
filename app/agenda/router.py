from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from supabase import create_client
import os
from typing import List, Optional

router = APIRouter(prefix="/agenda", tags=["agenda"])

supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

class AvailabilitySlot(BaseModel):
    day_of_week: int  # 0=Lundi, 6=Dimanche
    start_time: str   # "09:00"
    end_time: str     # "17:00"
    is_available: bool = True

class AvailabilityRequest(BaseModel):
    slots: List[AvailabilitySlot]

@router.post("/availability")
async def set_availability(
    request: AvailabilityRequest,
    current_user=Depends(get_current_user)
):
    doctor_id = current_user.id
    
    # Supprimer les anciennes disponibilités
    supabase.table("doctor_availability").delete().eq("doctor_id", doctor_id).execute()
    
    # Insérer les nouvelles
    slots = [
        {
            "doctor_id": doctor_id,
            "day_of_week": slot.day_of_week,
            "start_time": slot.start_time,
            "end_time": slot.end_time,
            "is_available": slot.is_available,
        }
        for slot in request.slots
    ]
    
    if slots:
        supabase.table("doctor_availability").insert(slots).execute()
    
    return {"message": "Disponibilités mises à jour"}

@router.get("/availability/{doctor_id}")
async def get_availability(doctor_id: str):
    result = supabase.table("doctor_availability").select("*").eq("doctor_id", doctor_id).execute()
    return result.data or []

@router.get("/my-availability")
async def get_my_availability(current_user=Depends(get_current_user)):
    doctor_id = current_user.id
    result = supabase.table("doctor_availability").select("*").eq("doctor_id", doctor_id).execute()
    return result.data or []