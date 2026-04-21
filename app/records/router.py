from fastapi import APIRouter, HTTPException, status, Depends
from supabase import create_client, Client
from app.config import settings
from app.auth.models import UserOut, UserRole
from app.auth.dependencies import get_current_user, require_doctor
from app.records.models import RecordCreate, RecordUpdate, RecordOut

router = APIRouter(prefix="/records", tags=["records"])

supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
)


@router.post("/", response_model=RecordOut, status_code=201)
async def create_record(
    body: RecordCreate,
    current_user: UserOut = Depends(require_doctor)
):
    """Médecin crée un dossier après la consultation."""
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

    return res.data[0]


@router.get("/", response_model=list[RecordOut])
async def list_records(
    current_user: UserOut = Depends(get_current_user)
):
    """Liste les dossiers selon le rôle."""
    try:
        if current_user.role == UserRole.patient:
            res = supabase.table("records")\
                .select("*")\
                .eq("patient_id", current_user.id)\
                .execute()
        else:
            res = supabase.table("records")\
                .select("*")\
                .eq("doctor_id", current_user.id)\
                .execute()
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    return res.data


@router.get("/{record_id}", response_model=RecordOut)
async def get_record(
    record_id: str,
    current_user: UserOut = Depends(get_current_user)
):
    """Détail d'un dossier médical."""
    res = supabase.table("records")\
        .select("*")\
        .eq("id", record_id)\
        .execute()

    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")

    return res.data[0]


@router.patch("/{record_id}", response_model=RecordOut)
async def update_record(
    record_id: str,
    body: RecordUpdate,
    current_user: UserOut = Depends(require_doctor)
):
    """Médecin met à jour un dossier."""
    update_data = {k: v for k, v in body.dict().items() if v is not None}

    if not update_data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Aucune donnée à mettre à jour")

    res = supabase.table("records")\
        .update(update_data)\
        .eq("id", record_id)\
        .execute()

    if not res.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Dossier introuvable")

    return res.data[0]