from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from app.auth.dependencies import get_current_user
from app.async_care.service import (
    create_case,
    get_patient_cases,
    get_doctor_cases,
    get_case,
    respond_to_case,
    escalate_case,
    get_questionnaire,
)
from app.audit.router import log_action
from app.database import get_supabase
from supabase import Client

router = APIRouter(prefix="/async-care", tags=["async-care"])

class CreateCaseRequest(BaseModel):
    specialty: str
    chief_complaint: str
    symptoms: List[str] = []
    questionnaire_answers: dict = {}

class RespondRequest(BaseModel):
    response: str

@router.get("/questionnaire/{specialty}")
async def questionnaire(specialty: str):
    return {"questions": get_questionnaire(specialty)}

@router.post("/cases")
async def create(req: CreateCaseRequest, request: Request, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    result = await create_case(
        patient_id=user.id,
        specialty=req.specialty,
        chief_complaint=req.chief_complaint,
        symptoms=req.symptoms,
        answers=req.questionnaire_answers,
    )
    await log_action(
        supabase=supabase,
        user_id=str(user.id),
        action="CREATE",
        table_name="async_care_cases",
        record_id=result.get("id") if isinstance(result, dict) else None,
        new_data=req.dict(),
        ip_address=request.client.host,
    )
    return result

@router.get("/cases/patient")
async def patient_cases(user=Depends(get_current_user)):
    return await get_patient_cases(user.id)

@router.get("/cases/doctor")
async def doctor_cases(user=Depends(get_current_user)):
    return await get_doctor_cases(user.id)

@router.get("/cases/{case_id}")
async def get_one(case_id: str, user=Depends(get_current_user)):
    result = await get_case(case_id)
    if not result:
        return {"error": "Dossier introuvable"}
    return result

@router.post("/cases/{case_id}/respond")
async def respond(case_id: str, req: RespondRequest, request: Request, user=Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    result = await respond_to_case(case_id, user.id, req.response)
    await log_action(
        supabase=supabase,
        user_id=str(user.id),
        action="UPDATE",
        table_name="async_care_cases",
        record_id=case_id,
        new_data={"response": req.response},
        ip_address=request.client.host,
    )
    return result

@router.patch("/cases/{case_id}/escalate")
async def escalate(case_id: str, user=Depends(get_current_user)):
    return await escalate_case(case_id)