import uuid
from unittest.mock import AsyncMock
from app.repositories.base import BaseRepository
from app.models.conversation import Conversation


def test_base_repository_tenant_scoping():
    mock_session = AsyncMock()
    tenant_a = uuid.uuid4()

    repo = BaseRepository(Conversation, mock_session, tenant_id=tenant_a)
    assert repo.tenant_id == tenant_a

    # So'rovga filtr qo'shilishini tekshirish
    from sqlalchemy import select
    base_query = select(Conversation)
    scoped_query = repo._apply_tenant_filter(base_query)

    # Scoped query ichida tenant_id filtri mavjudligini tasdiqlash
    sql_str = str(scoped_query)
    assert "conversations.tenant_id" in sql_str
