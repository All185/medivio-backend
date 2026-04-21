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
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_SERVICE_ROLE_KEY
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