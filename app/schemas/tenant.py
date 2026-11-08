import uuid
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TenantCreate(BaseModel):
    name: str = Field(..., min_length=2)
    slug: Optional[str] = None


class TenantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    is_active: bool
    role: Optional[str] = None


class TenantSwitchRequest(BaseModel):
    tenant_id: uuid.UUID
