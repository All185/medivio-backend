# app/auth/dependencies.py
import jwt
from jwt import PyJWKClient, ExpiredSignatureError, InvalidTokenError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.auth.models import UserOut, UserRole
from functools import lru_cache

bearer_scheme = HTTPBearer()

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token invalide ou expiré",
    headers={"WWW-Authenticate": "Bearer"},
)

JWKS_URL = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"

@lru_cache(maxsize=1)
def get_jwks_client() -> PyJWKClient:
    return PyJWKClient(JWKS_URL, cache_keys=True)

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserOut:
    token = credentials.credentials
    try:
        jwks_client = get_jwks_client()
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
            issuer=f"{settings.SUPABASE_URL}/auth/v1",
        )
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise CREDENTIALS_EXCEPTION

    user_metadata = payload.get("user_metadata", {})
    sub = payload.get("sub")
    email = payload.get("email")

    if not sub or not email:
        raise CREDENTIALS_EXCEPTION

    return UserOut(
        id=sub,
        email=email,
        full_name=user_metadata.get("full_name"),
        role=user_metadata.get("role", UserRole.patient),
    )

async def require_doctor(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    if current_user.role != UserRole.doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux médecins",
        )
    return current_user

async def require_patient(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    if current_user.role != UserRole.patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux patients",
        )
    return current_user