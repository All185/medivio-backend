import os
from fastapi import APIRouter, HTTPException, status, Depends
from supabase import create_client, Client
from app.config import settings
from app.auth.models import (
    RegisterRequest, LoginRequest,
    AuthResponse, UserOut, TokenResponse
)
from app.auth.dependencies import get_current_user
router = APIRouter(prefix="/auth", tags=["auth"])

# Client Supabase avec la clé service (admin) — jamais exposée au front
print("DEBUG SUPABASE_URL:", os.environ.get("SUPABASE_URL", "NOT FOUND"))
supabase: Client = create_client(
    os.environ.get("SUPABASE_URL", ""),
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
)

@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(body: RegisterRequest):
    """Inscription : crée l'utilisateur dans Supabase Auth + métadonnées."""
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
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Inscription échouée")

    # Si médecin, enregistrer la date de début d'essai
    if body.role.value == "doctor":
        try:
            from datetime import datetime, timezone
            supabase.table("specialist_profiles").update({
                "trial_start_date": datetime.now(timezone.utc).isoformat()
            }).eq("user_id", str(res.user.id)).execute()
        except Exception as e:
            print(f"Erreur trial_start_date: {e}")

    return _build_auth_response(res)


@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest):
    """Connexion : retourne access_token + refresh_token."""
    try:
        res = supabase.auth.sign_in_with_password({
            "email":    body.email,
            "password": body.password,
        })
    except Exception:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )

    if not res.user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Non autorisé")

    return _build_auth_response(res)


@router.post("/logout", status_code=204)
async def logout(current_user: UserOut = Depends(get_current_user)):
    """Révocation de session côté Supabase."""
    supabase.auth.sign_out()
    return


@router.get("/me", response_model=UserOut)
async def me(current_user: UserOut = Depends(get_current_user)):
    """Retourne le profil de l'utilisateur connecté."""
    return current_user


# ── Helper interne ────────────────────────────────

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

@router.get("/patients/search")
async def search_patients(q: str, user=Depends(get_current_user)):
    from supabase import create_client
    import os
    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_ROLE_KEY"))
    res = supabase.auth.admin.list_users()
    users = res if isinstance(res, list) else getattr(res, 'users', [])
    results = []
    for u in users:
        meta = u.user_metadata or {}
        full_name = meta.get('full_name', '') or ''
        email = u.email or ''
        if q.lower() in full_name.lower() or q.lower() in email.lower():
            results.append({
                "id": str(u.id),
                "full_name": full_name or email,
                "email": email,
            })
    return results[:10]