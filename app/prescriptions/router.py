from fastapi import APIRouter, Depends
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
async def create(req: CreatePrescriptionRequest, user=Depends(get_current_user)):
    return await create_prescription(
        doctor_id=user.id,
        patient_id=req.patient_id,
        items=[item.dict() for item in req.items],
        notes=req.notes,
    )

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
async def dispense(token: str, user=Depends(get_current_user)):
    return await dispense_prescription(token)