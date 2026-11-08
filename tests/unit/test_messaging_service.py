import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.instagram import InstagramAccount
from app.models.conversation import Conversation, Message
from app.models.flow import FlowDefinition, FlowVersion
from app.services.messaging_service import MessagingService
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository


@pytest.mark.asyncio
async def test_messaging_service_ignores_account_echo():
    """
    Biznes akkauntning o'zi yuborgan (echo) xabarlar bot tomonidan qayta ishlanmaydi.
    """
    mock_session = AsyncMock()
    service = MessagingService(mock_session)

    account = InstagramAccount(
        id=uuid.uuid4(),
        tenant_id=uuid.uuid4(),
        ig_user_id="business_123",
        page_id="page_123",
        username="business_account",
        encrypted_access_token="enc_token",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    result = await service.process_inbound_message(
        tenant_id=account.tenant_id,
        instagram_account=account,
        sender_id="business_123",  # Akkauntning o'zi
        message_text="Salom"
    )

    assert result["status"] == "echo_ignored"


@pytest.mark.asyncio
async def test_messaging_service_respects_human_takeover():
    """
    Suhbatda human_takeover yoqilgan bo'lsa, xabar saqlanadi lekin bot javob yubormaydi.
    """
    mock_session = AsyncMock()
    service = MessagingService(mock_session)

    tenant_id = uuid.uuid4()
    account_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    account = InstagramAccount(
        id=account_id,
        tenant_id=tenant_id,
        ig_user_id="business_123",
        page_id="page_123",
        username="business_account",
        encrypted_access_token="enc_token",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    conversation = Conversation(
        id=conv_id,
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        ig_recipient_id="customer_789",
        status="open",
        mode="human_takeover",  # Operator gaplashmoqda
        last_message_at=datetime.now(timezone.utc),
        messaging_window_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        unread_count=1
    )

    saved_msg = Message(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        conversation_id=conv_id,
        sender_type="contact",
        message_text="Menga operator kerak",
        status="delivered"
    )

    with patch.object(ConversationRepository, "get_or_create", return_value=conversation), \
         patch.object(ConversationRepository, "update_inbound_activity", return_value=conversation), \
         patch.object(MessageRepository, "save_message", return_value=saved_msg), \
         patch("app.repositories.outbox_repo.OutboxRepository.enqueue") as mock_enqueue:

        result = await service.process_inbound_message(
            tenant_id=tenant_id,
            instagram_account=account,
            sender_id="customer_789",
            message_text="Menga operator kerak",
            mid="mid.test_1"
        )

        assert result["status"] == "human_takeover_active"
        mock_enqueue.assert_not_called()


@pytest.mark.asyncio
async def test_messaging_service_triggers_bot_reply():
    """
    Bot rejimida kalit so'z mos kelsa, javob xabari Outbox ga joylanadi.
    """
    mock_session = AsyncMock()
    service = MessagingService(mock_session)

    tenant_id = uuid.uuid4()
    account_id = uuid.uuid4()
    conv_id = uuid.uuid4()

    account = InstagramAccount(
        id=account_id,
        tenant_id=tenant_id,
        ig_user_id="business_123",
        page_id="page_123",
        username="business_account",
        encrypted_access_token="enc_token",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    conversation = Conversation(
        id=conv_id,
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        ig_recipient_id="customer_789",
        status="open",
        mode="bot",
        last_message_at=datetime.now(timezone.utc),
        messaging_window_expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        unread_count=0
    )

    saved_msg = Message(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        conversation_id=conv_id,
        sender_type="contact",
        message_text="narx",
        status="delivered"
    )

    flow_def = FlowDefinition(id=uuid.uuid4(), tenant_id=tenant_id, instagram_account_id=account_id, name="DM Flow", is_active=True)
    flow_ver = FlowVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        flow_definition_id=flow_def.id,
        version_number=1,
        trigger_type="keyword_dm",
        trigger_config={"keywords": ["narx"], "match_type": "exact"},
        nodes=[
            {
                "id": "node_1",
                "type": "send_message",
                "data": {"text": "Assalomu alaykum! Kursimiz narxi 300,000 so'm."}
            }
        ],
        edges=[],
        is_published=True
    )

    with patch.object(ConversationRepository, "get_or_create", return_value=conversation), \
         patch.object(ConversationRepository, "update_inbound_activity", return_value=conversation), \
         patch.object(MessageRepository, "save_message", return_value=saved_msg), \
         patch.object(service, "_find_matching_dm_flow", return_value=(flow_def, flow_ver)), \
         patch("app.repositories.outbox_repo.OutboxRepository.enqueue", return_value=MagicMock()) as mock_enqueue:

        result = await service.process_inbound_message(
            tenant_id=tenant_id,
            instagram_account=account,
            sender_id="customer_789",
            message_text="narx",
            mid="mid.test_2"
        )

        assert result["status"] == "success"
        assert result["reply_action"] == "enqueued"
        mock_enqueue.assert_called_once()
