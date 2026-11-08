import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class FlowCreate(BaseModel):
    instagram_account_id: uuid.UUID
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None


class FlowVersionCreate(BaseModel):
    trigger_type: str = Field(default="keyword_dm")  # keyword_dm, comment_keyword, story_mention
    trigger_config: Dict[str, Any] = Field(default_factory=dict)
    nodes: List[Dict[str, Any]] = Field(..., min_length=1)
    edges: List[Dict[str, Any]] = Field(default_factory=list)


class FlowResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    instagram_account_id: uuid.UUID
    name: str
    description: Optional[str]
    is_active: bool
    active_version_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FlowVersionResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    flow_definition_id: uuid.UUID
    version_number: int
    trigger_type: str
    trigger_config: Dict[str, Any]
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]
    is_published: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
