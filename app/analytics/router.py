@router.get("/doctor/stats")
async def get_doctor_stats(current_user: dict = Depends(get_current_user)):
    doctor_id = current_user.get("id") or current_user.get("sub")
    if not doctor_id:
        raise HTTPException(status_code=401, detail="Non autorisé")
from fastapi import APIRouter, Depends, HTTPException
from app.auth.router import get_current_user
from supabase import create_client
import os
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])

supabase = create_client(
    os.environ.get("SUPABASE_URL"),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
)

@router.get("/doctor/stats")
async def get_doctor_stats(current_user: dict = Depends(get_current_user)):
    role = current_user.get("role") or current_user.get("user_metadata", {}).get("role", "")
    if role != "doctor":
        raise HTTPException(status_code=403, detail="Accès réservé aux médecins")

    doctor_id = current_user.get("id")

    appointments = supabase.table("appointments").select("*").eq("doctor_id", doctor_id).execute()
    data = appointments.data or []

    total = len(data)
    confirmed = len([a for a in data if a["status"] == "confirmed"])
    completed = len([a for a in data if a["status"] == "completed"])
    cancelled = len([a for a in data if a["status"] == "cancelled"])
    pending = len([a for a in data if a["status"] == "pending"])

    now = datetime.now()
    first_day = now.replace(day=1).isoformat()
    this_month = len([a for a in data if a.get("scheduled_at", "") >= first_day])

    week_ago = (now - timedelta(days=7)).isoformat()
    this_week = len([a for a in data if a.get("scheduled_at", "") >= week_ago])

    return {
        "total": total,
        "confirmed": confirmed,
        "completed": completed,
        "cancelled": cancelled,
        "pending": pending,
        "this_month": this_month,
        "this_week": this_week,
        "completion_rate": round((completed / total * 100) if total > 0 else 0, 1),
        "cancellation_rate": round((cancelled / total * 100) if total > 0 else 0, 1),
    }