from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.auth.dependencies import get_current_user
from app.senior.service import (
    get_or_create_profile,
    record_interaction,
    set_level,
    get_family_access,
    add_family_member,
    remove_family_member,
    get_senior_dashboard,
)

router = APIRouter(prefix="/senior", tags=["senior"])

class InteractionRequest(BaseModel):
    action: str
    success: bool = True

class SetLevelRequest(BaseModel):
    patient_id: str
    level: int

class FamilyMemberRequest(BaseModel):
    family_email: str
    family_name: str

@router.get("/profile")
async def get_profile(user=Depends(get_current_user)):
    return await get_or_create_profile(user.id)

@router.post("/interaction")
async def log_interaction(req: InteractionRequest, user=Depends(get_current_user)):
    return await record_interaction(user.id, req.action, req.success)

@router.patch("/level")
async def update_level(req: SetLevelRequest, user=Depends(get_current_user)):
    return await set_level(req.patient_id, req.level)

@router.get("/family")
async def get_family(user=Depends(get_current_user)):
    return await get_family_access(user.id)

@router.post("/family")
async def add_family(req: FamilyMemberRequest, user=Depends(get_current_user)):
    return await add_family_member(user.id, req.family_email, req.family_name)

@router.delete("/family/{access_id}")
async def remove_family(access_id: str, user=Depends(get_current_user)):
    return await remove_family_member(access_id)

@router.get("/dashboard/{patient_id}")
async def get_dashboard(patient_id: str, user=Depends(get_current_user)):
    return await get_senior_dashboard(patient_id)