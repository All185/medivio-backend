from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List
from app.auth.dependencies import get_current_user
from app.marketplace.service import (
    get_all_specialists,
    get_specialist,
    create_specialist_profile,
    claim_profile,
    add_review,
    match_specialist,
)

router = APIRouter(prefix="/marketplace", tags=["marketplace"])

class CreateProfileRequest(BaseModel):
    full_name: str
    specialty: str
    sub_specialty: Optional[str] = None
    bio: Optional[str] = None
    languages: Optional[List[str]] = ["fr"]
    consultation_price: Optional[float] = None
    years_experience: Optional[int] = None
    clinic_name: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = "France"
    rpps_number: Optional[str] = None

class ReviewRequest(BaseModel):
    rating: int
    comment: Optional[str] = ""

class MatchRequest(BaseModel):
    symptoms: str

@router.get("/specialists")
async def list_specialists(specialty: Optional[str] = None, city: Optional[str] = None):
    return await get_all_specialists(specialty=specialty, city=city)

@router.get("/specialists/{specialist_id}")
async def get_specialist_profile(specialist_id: str):
    result = await get_specialist(specialist_id)
    if not result:
        return {"error": "Specialiste introuvable"}
    return result

@router.post("/specialists")
async def create_profile(req: CreateProfileRequest, user=Depends(get_current_user)):
    data = req.dict()
    data["user_id"] = user.id
    data["is_claimed"] = True
    return await create_specialist_profile(data)

@router.patch("/specialists/{specialist_id}/claim")
async def claim(specialist_id: str, user=Depends(get_current_user)):
    return await claim_profile(specialist_id, user.id)

@router.post("/specialists/{specialist_id}/review")
async def review(specialist_id: str, req: ReviewRequest, user=Depends(get_current_user)):
    return await add_review(specialist_id, user.id, req.rating, req.comment)

@router.post("/match")
async def match(req: MatchRequest, user=Depends(get_current_user)):
    return await match_specialist(req.symptoms)