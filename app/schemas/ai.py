import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AIAgentConfigBase(BaseModel):
    model_name: str = Field(default="meta-llama/llama-3.3-70b-instruct")
    system_prompt: str = Field(..., description="AI agentining xulq-atvori va yo'riqnomasi")
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=350, ge=50, le=2000)
    lead_capture_enabled: bool = True
    is_active: bool = True


class AIAgentConfigUpdate(BaseModel):
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(default=None, ge=50, le=2000)
    lead_capture_enabled: Optional[bool] = None
    is_active: Optional[bool] = None


class AIAgentConfigResponse(AIAgentConfigBase):
    id: uuid.UUID
    tenant_id: uuid.UUID
    instagram_account_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeSourceCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=255)
    source_type: str = Field(default="raw_text")
    content: str = Field(..., min_length=10, description="Bilim manbai to'liq matni")


class KnowledgeSourceResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    title: str
    source_type: str
    processing_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
