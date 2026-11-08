import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.instagram import InstagramAccount
from app.models.conversation import Conversation
from app.models.ai_config import AIAgentConfig
from app.services.ai_agent_service import AIAgentService
from app.repositories.ai_repo import AIRepository
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.lead_repo import LeadRepository


@pytest.mark.asyncio
async def test_ai_agent_service_live_agent_handoff():
    """
    Mijoz 'operator' so'raganda suhbat rejimi human_takeover ga o'tadi
    va OpenRouter ga so'rov bormaydi.
    """
    mock_session = AsyncMock()
    mock_openrouter = AsyncMock()
    service = AIAgentService(mock_session, openrouter_client=mock_openrouter)

    tenant_id = uuid.uuid4()
    account_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    account = InstagramAccount(
        id=account_id,
        tenant_id=tenant_id,
        ig_user_id="page_123",
        page_id="page_123",
        username="business",
        encrypted_access_token="enc_token",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    conversation = Conversation(
        id=conv_id,
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        ig_recipient_id="customer_1",
        status="open",
        mode="ai_assistant",
        last_message_at=datetime.now(timezone.utc),
        messaging_window_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        unread_count=0
    )

    with patch.object(ConversationRepository, "set_mode", return_value=True) as mock_set_mode, \
         patch("app.repositories.outbox_repo.OutboxRepository.enqueue", return_value=MagicMock()) as mock_outbox:

        result = await service.process_ai_interaction(
            tenant_id=tenant_id,
            instagram_account=account,
            conversation=conversation,
            user_message_text="Menga jonli operator kerak, iltimos ulab bering"
        )

        assert result["status"] == "handoff_triggered"
        assert result["conversation_mode"] == "human_takeover"
        mock_set_mode.assert_called_once_with(tenant_id, conv_id, "human_takeover")
        mock_outbox.assert_called_once()
        # OpenRouter ga so'rov bormasligi kerak
        mock_openrouter.complete.assert_not_called()


@pytest.mark.asyncio
async def test_ai_agent_service_lead_capture_and_generation():
    """
    Mijoz telefon raqami kiritganda, lead CRM ga yoziladi va AI javobi Outbox ga navbatlanadi.
    """
    mock_session = AsyncMock()
    mock_openrouter = AsyncMock()
    mock_openrouter.complete.return_value = {
        "content": "Rahmat Ali! Mutaxassisimiz tez orada sizga qo'ng'iroq qiladi.",
        "model": "meta-llama/llama-3.3-70b-instruct"
    }

    service = AIAgentService(mock_session, openrouter_client=mock_openrouter)

    tenant_id = uuid.uuid4()
    account_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    account = InstagramAccount(
        id=account_id,
        tenant_id=tenant_id,
        ig_user_id="page_123",
        page_id="page_123",
        username="business",
        encrypted_access_token="enc_token",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    conversation = Conversation(
        id=conv_id,
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        ig_recipient_id="customer_1",
        status="open",
        mode="ai_assistant",
        last_message_at=datetime.now(timezone.utc),
        messaging_window_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        unread_count=0
    )

    ai_config = AIAgentConfig(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        system_prompt="Siz savdo yordamchisisiz.",
        model_name="meta-llama/llama-3.3-70b-instruct",
        temperature=0.7,
        max_tokens=350,
        lead_capture_enabled=True,
        is_active=True
    )

    with patch.object(AIRepository, "get_config_by_account", return_value=ai_config), \
         patch.object(LeadRepository, "upsert_lead", return_value=MagicMock()) as mock_upsert_lead, \
         patch("app.repositories.message_repo.MessageRepository.get_messages_by_conversation", return_value=[]), \
         patch("app.repositories.outbox_repo.OutboxRepository.enqueue", return_value=MagicMock()) as mock_outbox:

        result = await service.process_ai_interaction(
            tenant_id=tenant_id,
            instagram_account=account,
            conversation=conversation,
            user_message_text="Mening ismim Ali, raqamim 901234567, kursga yozilmoqchiman"
        )

        assert result["status"] == "success"
        assert "Ali" in result["reply_text"]
        # Lead CRM ga kiritilganini tekshirish
        mock_upsert_lead.assert_called_once()
        assert mock_upsert_lead.call_args[1]["full_name"] == "Ali"
        assert mock_upsert_lead.call_args[1]["phone_number"] == "+998901234567"
        mock_outbox.assert_called_once()


@pytest.mark.asyncio
async def test_ai_agent_service_disabled_config():
    """AI sozlamasi o'chiq (is_active=False) bo'lsa hech qanday generatsiya bo'lmaydi"""
    mock_session = AsyncMock()
    mock_openrouter = AsyncMock()
    service = AIAgentService(mock_session, openrouter_client=mock_openrouter)

    tenant_id = uuid.uuid4()
    account_id = uuid.uuid4()

    account = InstagramAccount(
        id=account_id,
        tenant_id=tenant_id,
        ig_user_id="page_123",
        page_id="page_123",
        username="business",
        encrypted_access_token="enc_token",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    conversation = Conversation(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        ig_recipient_id="customer_1",
        status="open",
        mode="ai_assistant",
        last_message_at=datetime.now(timezone.utc),
        messaging_window_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        unread_count=0
    )

    ai_config = AIAgentConfig(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        system_prompt="Prompt",
        is_active=False  # O'chiq
    )

    with patch.object(AIRepository, "get_config_by_account", return_value=ai_config):
        result = await service.process_ai_interaction(
            tenant_id=tenant_id,
            instagram_account=account,
            conversation=conversation,
            user_message_text="Salom"
        )

    assert result["status"] == "ai_disabled"
    mock_openrouter.complete.assert_not_called()
