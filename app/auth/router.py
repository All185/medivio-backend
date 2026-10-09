import os
import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status, Depends, Query
from supabase import create_client, Client
from app.config import settings
from app.auth.models import (
    RegisterRequest, LoginRequest,
    AuthResponse, UserOut, TokenResponse, DoctorRequestIn
)
from app.auth.dependencies import get_current_user
import resend

router = APIRouter(prefix="/auth", tags=["auth"])

resend.api_key = os.environ.get("RESEND_API_KEY")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "contact@medivio.care")
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "https://medivio.care")

supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
)


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest):
    try:
        res = supabase.auth.sign_up({
            "email":    body.email,
            "password": body.password,
            "options": {
                "data": {
                    "full_name": body.full_name,
                    "role":      body.role.value,
                }
            }
        })
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    if not res.user:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Inscription echouee")

    if body.role.value == "doctor":
        try:
            supabase.table("specialist_profiles").update({
                "trial_start_date": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", str(res.user.id)).execute()
        except Exception as e:
            print(f"Erreur trial_start_date: {e}")

    return _build_auth_response(res)


@router.post("/request-access", status_code=201)
async def request_access(body: DoctorRequestIn):
    existing = supabase.table("doctor_requests").select("id").eq("email", body.email).execute()
    if existing.data:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Une demande existe deja pour cet email.")

    req = supabase.table("doctor_requests").insert({
        "first_name": body.first_name,
        "last_name":  body.last_name,
        "email":      body.email,
        "specialty":  body.specialty,
        "rpps":       body.rpps,
        "cabinet":    body.cabinet,
        "status":     "pending",
    }).execute()

    request_id = req.data[0]["id"]
    approve_url = f"{FRONTEND_URL}/api/v1/auth/approve/{request_id}?secret={ADMIN_SECRET}"
    reject_url  = f"{FRONTEND_URL}/api/v1/auth/reject/{request_id}?secret={ADMIN_SECRET}"

    resend.Emails.send({
        "from": "Medivio <contact@medivio.care>",
        "to":   ADMIN_EMAIL,
        "subject": f"Nouvelle demande acces - Dr. {body.first_name} {body.last_name}",
        "html": f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #009E88, #2B5EF8); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0;">Medivio</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0;">Nouvelle demande d acces</p>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #E2E8F0;">
                <h2 style="color: #1E293B;">Dr. {body.first_name} {body.last_name}</h2>
                <table style="width:100%; border-collapse: collapse; margin-bottom: 24px;">
                    <tr><td style="padding: 8px; color: #64748B;">Email</td><td style="padding: 8px; font-weight: bold;">{body.email}</td></tr>
                    <tr style="background:#F8FAFC"><td style="padding: 8px; color: #64748B;">Specialite</td><td style="padding: 8px; font-weight: bold;">{body.specialty}</td></tr>
                    <tr><td style="padding: 8px; color: #64748B;">N RPPS</td><td style="padding: 8px; font-weight: bold;">{body.rpps}</td></tr>
                    <tr style="background:#F8FAFC"><td style="padding: 8px; color: #64748B;">Cabinet</td><td style="padding: 8px; font-weight: bold;">{body.cabinet or "-"}</td></tr>
                </table>
                <div style="text-align: center;">
                    <a href="{approve_url}" style="display: inline-block; background: #009E88; color: white; padding: 14px 24px; border-radius: 10px; text-decoration: none; font-weight: bold; margin-right: 12px;">Approuver</a>
                    <a href="{reject_url}" style="display: inline-block; background: #EF4444; color: white; padding: 14px 24px; border-radius: 10px; text-decoration: none; font-weight: bold;">Refuser</a>
                </div>
            </div>
        </div>
        """
    })

    return {"success": True, "message": "Demande envoyee. Vous recevrez une reponse par email."}


@router.get("/approve/{request_id}")
async def approve_request(request_id: str, secret: str = Query(...)):
    if secret != ADMIN_SECRET:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Non autorise")

    req = supabase.table("doctor_requests").select("*").eq("id", request_id).single().execute()
    if not req.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Demande introuvable")

    data = req.data
    if data["status"] != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Demande deja traitee")

    tmp_password = secrets.token_urlsafe(16)
    try:
        user_res = supabase.auth.admin.create_user({
            "email":         data["email"],
            "password":      tmp_password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": f"{data['first_name']} {data['last_name']}",
                "role":      "doctor",
                "specialty": data["specialty"],
                "rpps":      data["rpps"],
            }
        })
    except Exception as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))

    user_id = user_res.user.id

    try:
        supabase.table("specialist_profiles").upsert({
            "user_id":          str(user_id),
            "trial_start_date": datetime.now(timezone.utc).isoformat()
        }).execute()
    except Exception as e:
        print(f"Erreur trial_start_date: {e}")

    try:
        link_res = supabase.auth.admin.generate_link({
            "type":  "recovery",
            "email": data["email"],
        })
        reset_link = link_res.properties.action_link
    except Exception:
        reset_link = f"{FRONTEND_URL}/reset-password"

    supabase.table("doctor_requests").update({"status": "approved"}).eq("id", request_id).execute()

    resend.Emails.send({
        "from": "Medivio <contact@medivio.care>",
        "to":   data["email"],
        "subject": "Bienvenue sur Medivio - Activez votre compte",
        "html": f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #009E88, #2B5EF8); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0;">Medivio</h1>
                <p style="color: rgba(255,255,255,0.8); margin: 5px 0 0;">Telemedicine augmentee par l IA</p>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #E2E8F0;">
                <h2 style="color: #1E293B;">Bonjour Dr. {data["first_name"]} {data["last_name"]},</h2>
                <p style="color: #64748B;">Votre demande d acces a ete approuvee. Vous beneficiez d un acces complet a Medivio pendant <strong>3 mois</strong>.</p>
                <p style="color: #64748B;">Cliquez ci-dessous pour definir votre mot de passe et acceder a votre espace.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{reset_link}" style="display: inline-block; background: linear-gradient(135deg, #009E88, #2B5EF8); color: white; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: bold;">Activer mon compte</a>
                </div>
                <p style="color: #94A3B8; font-size: 12px; text-align: center;">Ce lien est valable 24h. Medivio - medivio.care</p>
            </div>
        </div>
        """
    })

    return {"success": True, "message": f"Compte cree et email envoye a {data['email']}"}


@router.get("/reject/{request_id}")
async def reject_request(request_id: str, secret: str = Query(...)):
    if secret != ADMIN_SECRET:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Non autorise")

    req = supabase.table("doctor_requests").select("*").eq("id", request_id).single().execute()
    if not req.data:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Demande introuvable")

    data = req.data
    if data["status"] != "pending":
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Demande deja traitee")

    supabase.table("doctor_requests").update({"status": "rejected"}).eq("id", request_id).execute()

    resend.Emails.send({
        "from": "Medivio <contact@medivio.care>",
        "to":   data["email"],
        "subject": "Votre demande d acces Medivio",
        "html": f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #009E88, #2B5EF8); padding: 30px; text-align: center; border-radius: 12px 12px 0 0;">
                <h1 style="color: white; margin: 0;">Medivio</h1>
            </div>
            <div style="background: white; padding: 30px; border-radius: 0 0 12px 12px; border: 1px solid #E2E8F0;">
                <h2 style="color: #1E293B;">Bonjour Dr. {data["first_name"]} {data["last_name"]},</h2>
                <p style="color: #64748B;">Apres examen, nous ne sommes pas en mesure de donner suite a votre demande pour le moment.</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://medivio.care/contact" style="display: inline-block; background: linear-gradient(135deg, #009E88, #2B5EF8); color: white; padding: 14px 32px; border-radius: 10px; text-decoration: none; font-weight: bold;">Nous contacter</a>
                </div>
            </div>
        </div>
        """
    })

    return {"success": True, "message": "Demande refusee, email envoye."}


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    try:
        res = supabase.auth.sign_in_with_password({
            "email":    body.email,
            "password": body.password,
        })
    except Exception:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect")

    if not res.user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Non autorise")

    return _build_auth_response(res)


@router.post("/logout", status_code=204)
async def logout(current_user: UserOut = Depends(get_current_user)):
    supabase.auth.sign_out()
    return


@router.get("/me", response_model=UserOut)
async def me(current_user: UserOut = Depends(get_current_user)):
    return current_user


@router.get("/patients/search")
async def search_patients(q: str, user=Depends(get_current_user)):
    res = supabase.auth.admin.list_users()
    users = res if isinstance(res, list) else getattr(res, "users", [])
    results = []
    for u in users:
        meta = u.user_metadata or {}
        full_name = meta.get("full_name", "") or ""
        email = u.email or ""
        if q.lower() in full_name.lower() or q.lower() in email.lower():
            results.append({"id": str(u.id), "full_name": full_name or email, "email": email})
    return results[:10]


def _build_auth_response(res) -> AuthResponse:
    user = res.user
    meta = user.user_metadata or {}
    session = res.session
    return AuthResponse(
        user=UserOut(
            id=user.id,
            email=user.email,
            full_name=meta.get("full_name"),
            role=meta.get("role", "patient"),
        ),
        token=TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in,
        )
    )
