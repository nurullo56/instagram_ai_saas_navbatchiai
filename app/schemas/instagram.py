import uuid
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class InstagramOAuthUrlResponse(BaseModel):
    authorization_url: str


class InstagramOAuthExchangeRequest(BaseModel):
    code: str = Field(..., min_length=1)
    redirect_uri: str = Field(..., min_length=1)


class InstagramAccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    ig_user_id: str
    page_id: str
    username: str
    name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    webhook_subscribed: bool
    is_active: bool
    token_expires_at: datetime
    created_at: datetime
