import os
from fastapi import APIRouter, HTTPException, status, Depends, Request
from supabase import create_client, Client
from app.config import settings
from app.auth.models import UserOut, UserRole
from app.auth.dependencies import get_current_user, require_doctor
from app.records.models import RecordCreate, RecordUpdate, RecordOut
from app.audit.router import log_action

router = APIRouter(prefix="/records", tags=["records"])

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)

@router.post("/", response_model=RecordOut, status_code=201)
async def create_record(
    body: RecordCreate,
    request: Request,
    current_user: UserOut = Depends(require_doctor)
):
    try:
        res = supabase.table("records").insert({
            "appointment_id": body.appointment_id,
            "patient_id":     body.patient_id,
            "doctor_id":      current_user.id,
            "diagnosis":      body.diagnosis,
            "prescription":   body.prescription,
            "notes":          body.notes,
        }).execute()
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    await log_action(
        supabase=supabase,
        user_id=str(current_user.id),
        action="CREATE",
        table_name="records",
        record_id=res.data[0].get("id"),
        new_data=body.dict(),
        ip_address=request.client.host,
    )
    return res.data[0]

@router.get("/", response_model=list[RecordOut])
async def list_records(current_user: UserOut = Depends(get_current_user)):
    try:
        if current_user.role == UserRole.patient:
            res = supabase.table("records").select("*").eq("patient_id", current_user.id).execute()
        else:
            res = supabase.table("records").select("*").eq("doctor_id", current_user.id).execute()
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    return res.data

@router.get("/{record_id}", response_model=RecordOut)
async def get_record(record_id: str, current_user: UserOut = Depends(get_current_user)):
    res = supabase.table("records").select("*").eq("id", record_id).execute()
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")
    return res.data[0]

@router.patch("/{record_id}", response_model=RecordOut)
async def update_record(
    record_id: str,
    body: RecordUpdate,
    request: Request,
    current_user: UserOut = Depends(require_doctor)
):
    update_data = {k: v for k, v in body.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Aucune donnée à mettre à jour")

    # Récupérer l'ancienne valeur avant modification
    old = supabase.table("records").select("*").eq("id", record_id).execute()
    old_data = old.data[0] if old.data else None

    res = supabase.table("records").update(update_data).eq("id", record_id).execute()
    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")

    await log_action(
        supabase=supabase,
        user_id=str(current_user.id),
        action="UPDATE",
        table_name="records",
        record_id=record_id,
        old_data=old_data,
        new_data=update_data,
        ip_address=request.client.host,
    )
    return res.data[0]