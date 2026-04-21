from pydantic import BaseModel, EmailStr
from enum import Enum
from typing import Optional


class UserRole(str, Enum):
    patient = "patient"
    doctor  = "doctor"


# ── Requêtes entrantes ────────────────────────────

class RegisterRequest(BaseModel):
    email:    EmailStr
    password: str
    full_name: str
    role:     UserRole = UserRole.patient


class LoginRequest(BaseModel):
    email:    EmailStr
    password: str


# ── Réponses sortantes ────────────────────────────

class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"
    expires_in:    int


class UserOut(BaseModel):
    id:        str
    email:     str
    full_name: Optional[str]
    role:      UserRole


class AuthResponse(BaseModel):
    user:  UserOut
    token: TokenResponse