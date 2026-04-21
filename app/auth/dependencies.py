from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from app.config import settings
from app.auth.models import UserOut, UserRole

bearer_scheme = HTTPBearer()

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token invalide ou expiré",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> UserOut:
    """Décode le JWT Supabase et retourne l'utilisateur courant."""
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},  # Supabase n'inclut pas toujours aud
        )
    except JWTError:
        raise CREDENTIALS_EXCEPTION

    user_metadata = payload.get("user_metadata", {})

    return UserOut(
        id=payload.get("sub"),
        email=payload.get("email"),
        full_name=user_metadata.get("full_name"),
        role=user_metadata.get("role", UserRole.patient),
    )


async def require_doctor(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    """Guard : réserve la route aux médecins uniquement."""
    if current_user.role != UserRole.doctor:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux médecins",
        )
    return current_user


async def require_patient(
    current_user: UserOut = Depends(get_current_user),
) -> UserOut:
    """Guard : réserve la route aux patients uniquement."""
    if current_user.role != UserRole.patient:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux patients",
        )
    return current_user