from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.emergency.service import analyze_emergency, notify_doctor
from supabase import create_client
import os

router = APIRouter(prefix="/emergency", tags=["emergency"])

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))

class EmergencyRequest(BaseModel):
    symptoms: str
    pain_level: int
    patient_id: str

class EmergencyResponse(BaseModel):
    level: str
    recommendation: str
    call_samu: bool
    available_doctor_id: str | None

@router.post("/analyze", response_model=EmergencyResponse)
async def analyze(req: EmergencyRequest, user=Depends(get_current_user)):
    result = await analyze_emergency(req.symptoms, req.pain_level)

    supabase.table("emergencies").insert({
        "patient_id": req.patient_id,
        "symptoms": req.symptoms,
        "pain_level": req.pain_level,
        "level": result["level"],
        "recommendation": result["recommendation"],
    }).execute()

    doctor_id = None
    if result["level"] != "critical":
        doctor_id = await notify_doctor(req.patient_id, result["level"])

    return EmergencyResponse(
        level=result["level"],
        recommendation=result["recommendation"],
        call_samu=result["level"] == "critical",
        available_doctor_id=doctor_id,
    )

@router.get("/active")
async def get_active_emergencies(user=Depends(get_current_user)):
    res = supabase.table("emergencies")\
        .select("*, patients(full_name)")\
        .eq("handled", False)\
        .order("created_at", desc=True)\
        .execute()
    return res.data
    
    @router.patch("/{emergency_id}/handled")
async def mark_handled(emergency_id: str, user=Depends(get_current_user)):
    supabase.table("emergencies")\
        .update({"handled": True})\
        .eq("id", emergency_id)\
        .execute()
    return {"success": True}