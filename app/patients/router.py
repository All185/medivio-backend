import os
import secrets
from fastapi import APIRouter, HTTPException, status, Depends
from supabase import create_client, Client
from app.auth.dependencies import get_current_user
from app.auth.models import UserOut
from pydantic import BaseModel, EmailStr
import resend

router = APIRouter(prefix="/patients", tags=["patients"])

resend.api_key = os.environ.get("RESEND_API_KEY")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://medivio.care")

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
)


class InvitePatientRequest(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str


@router.post("/invite", status_code=201)
async def invite_patient(body: InvitePatientRequest, doctor: UserOut = Depends(get_current_user)):
    if doctor.role != "doctor":
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Reserve aux medecins")

    tmp_password = secrets.token_urlsafe(16)

    try:
        user_res = supabase.auth.admin.create_user({
            "email":         body.email,
            "password":      tmp_password,
            "email_confirm": True,
            "user_metadata": {
                "full_name":  f"{body.first_name} {body.last_name}",
                "role":       "patient",
                "invited_by": str(doctor.id),
            }
        })
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        link_res = supabase.auth.admin.generate_link({
            "type":  "recovery",
            "email": body.email,
        })
        reset_link = link_res.properties.action_link
    except Exception:
        reset_link = f"{FRONTEND_URL}/reset-password"

    doctor_name = doctor.full_name or "Votre medecin"

    resend.Emails.send({
        "from": "Medivio <contact@medivio.care>",
        "to":   body.email,
        "subject": f"{doctor_name} vous invite sur Medivio",
        "html": f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #009E88, #2B5EF8); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0;">Medivio</h1>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #E2E8F0;">
                <h2 style="color: #1E293B;">Bonjour {body.first_name},</h2>
                <p style="color: #64748B;"><strong>{doctor_name}</strong> vous invite a rejoindre Medivio.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #009E88, #2B5EF8); color: white; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: bold;">
                        Creer mon compte
                    </a>
                </div>
                <p style="color: #94A3B8; font-size: 12px; text-align: center;">Ce lien est valable 24h.</p>
            </div>
        </div>
        """
    })

    return {"success": True, "message": f"Invitation envoyee a {body.email}"}
