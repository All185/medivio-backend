from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from supabase import create_client
from app.auth.dependencies import get_current_user

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

router = APIRouter(prefix="/waiting", tags=["waiting"])

class JoinWaitingRoom(BaseModel):
    appointment_id: Optional[int] = None
    symptoms: Optional[str] = None
    pain_level: Optional[int] = 5
    medications: Optional[str] = None

class UpdateStatus(BaseModel):
    status: str

@router.post("/join")
async def join_waiting_room(data: JoinWaitingRoom, user=Depends(get_current_user)):
    existing = supabase.table("waiting_room").select("*").eq("patient_id", user["id"]).eq("status", "waiting").execute()
    if existing.data:
        return existing.data[0]

    result = supabase.table("waiting_room").insert({
        "patient_id": user["id"],
        "appointment_id": data.appointment_id,
        "symptoms": data.symptoms,
        "pain_level": data.pain_level,
        "medications": data.medications,
        "status": "waiting"
    }).execute()

    return result.data[0]

@router.get("/list")
async def list_waiting_room(user=Depends(get_current_user)):
    result = supabase.table("waiting_room").select("*").eq("status", "waiting").order("joined_at").execute()
    return result.data

@router.patch("/{entry_id}/status")
async def update_status(entry_id: str, data: UpdateStatus, user=Depends(get_current_user)):
    result = supabase.table("waiting_room").update({
        "status": data.status,
        "doctor_id": user["id"]
    }).eq("id", entry_id).execute()
    return result.data[0]

@router.delete("/leave")
async def leave_waiting_room(user=Depends(get_current_user)):
    supabase.table("waiting_room").update({"status": "done"}).eq("patient_id", user["id"]).eq("status", "waiting").execute()
    return {"message": "Vous avez quitté la salle d'attente"}
