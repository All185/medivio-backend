from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from app.auth.dependencies import get_current_user
from app.prescriptions.service import (
    create_prescription,
    get_patient_prescriptions,
    get_doctor_prescriptions,
    verify_prescription,
    dispense_prescription,
)
from app.audit.router import log_action
from app.database import get_supabase
from supabase import Client

router = APIRouter(prefix="/prescriptions", tags=["prescriptions"])

class PrescriptionItem(BaseModel):
    medication: str
    dosage: str
    frequency: str
    duration: str
    instructions: Optional[str] = ""

class CreatePrescriptionRequest(BaseModel):
    patient_id: str
    items: List[PrescriptionItem]
    notes: Optional[str] = ""

@router.post("/create")
async def create(req: CreatePrescriptionRequest, request: Request, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    result = await create_prescription(
        doctor_id=user.id,
        patient_id=req.patient_id,
        items=[item.dict() for item in req.items],
        notes=req.notes,
    )
    await log_action(
        supabase=supabase,
        user_id=str(user.id),
        action="CREATE",
        table_name="prescriptions",
        record_id=result.get("id") if isinstance(result, dict) else None,
        new_data=req.dict(),
        ip_address=request.client.host,
    )
    return result

@router.get("/patient")
async def get_patient(user=Depends(get_current_user)):
    return await get_patient_prescriptions(user.id)

@router.get("/doctor")
async def get_doctor(user=Depends(get_current_user)):
    return await get_doctor_prescriptions(user.id)

@router.get("/verify/{token}")
async def verify(token: str):
    result = await verify_prescription(token)
    if not result:
        return {"error": "Ordonnance introuvable ou invalide"}
    return result

@router.patch("/dispense/{token}")
async def dispense(token: str, request: Request, supabase: Client = Depends(get_supabase)):
    result = await dispense_prescription(token)
    await log_action(
        supabase=supabase,
        user_id="pharmacist",
        action="UPDATE",
        table_name="prescriptions",
        new_data={"token": token, "status": "dispensed"},
        ip_address=request.client.host,
    )
    return result