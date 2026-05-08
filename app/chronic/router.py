from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.auth.dependencies import get_current_user
from app.chronic.service import (
    add_vital_record,
    get_vital_records,
    get_alerts,
    mark_alert_read,
    get_doctor_patients_vitals,
)

router = APIRouter(prefix="/chronic", tags=["chronic"])

class VitalRecordRequest(BaseModel):
    source: Optional[str] = "manual"
    blood_pressure_systolic: Optional[int] = None
    blood_pressure_diastolic: Optional[int] = None
    heart_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    blood_glucose: Optional[float] = None
    weight: Optional[float] = None
    respiratory_rate: Optional[int] = None
    temperature: Optional[float] = None
    notes: Optional[str] = None

@router.post("/vitals")
async def add_vitals(req: VitalRecordRequest, user=Depends(get_current_user)):
    return await add_vital_record(user.id, req.dict(exclude_none=True))

@router.get("/vitals")
async def get_vitals(user=Depends(get_current_user)):
    return await get_vital_records(user.id)

@router.get("/alerts")
async def get_patient_alerts(user=Depends(get_current_user)):
    return await get_alerts(user.id)

@router.patch("/alerts/{alert_id}/read")
async def read_alert(alert_id: str, user=Depends(get_current_user)):
    return await mark_alert_read(alert_id)

@router.get("/doctor/overview")
async def doctor_overview(user=Depends(get_current_user)):
    return await get_doctor_patients_vitals(user.id)