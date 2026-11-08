import uuid
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Kamida 8 ta belgi")
    full_name: str = Field(..., min_length=2)
    company_name: str = Field(..., min_length=2, description="Kompaniya/Tenant nomi")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: Optional[str] = None
    is_superadmin: bool
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
