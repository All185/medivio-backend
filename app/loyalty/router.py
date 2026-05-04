from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.auth.dependencies import get_current_user
from app.loyalty.service import add_points, get_loyalty

router = APIRouter(prefix="/loyalty", tags=["loyalty"])

class AddPointsRequest(BaseModel):
    patient_id: str
    action: str

@router.post("/add-points")
async def add_points_endpoint(req: AddPointsRequest, user=Depends(get_current_user)):
    return await add_points(req.patient_id, req.action)

@router.get("/me")
async def get_my_loyalty(user=Depends(get_current_user)):
    return await get_loyalty(user.id)