import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
import pytest
from app.models.instagram import InstagramAccount
from app.models.conversation import Conversation
from app.models.comment import CommentLog
from app.models.outbox import OutboxEvent
from app.services.outbound_dispatcher import OutboundDispatcher
from app.security.encryption import TokenEncryptor
from app.integrations.meta.exceptions import (
    MetaRateLimitException,
    MetaMessagingWindowException,
    MetaPermanentException,
    MetaNetworkTimeoutException,
)


@pytest.mark.asyncio
async def test_dispatcher_enforces_24h_window_on_direct_message():
    """
    Suhbatda 24 soatlik Meta oynasi tugagan bo'lsa, xabar Meta API ga jo'natilmaydi,
    outbox holati esa 'rejected_permanent' ga o'tkaziladi.
    """
    mock_session = AsyncMock()
    mock_messaging_client = AsyncMock()
    dispatcher = OutboundDispatcher(mock_session, messaging_client=mock_messaging_client)

    tenant_id = uuid.uuid4()
    account_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    event_id = uuid.uuid4()

    # Eskirgan 24h oyna
    expired_time = datetime.now(timezone.utc) - timedelta(hours=25)
    conversation = Conversation(
        id=conv_id,
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        ig_recipient_id="recipient_123",
        status="open",
        mode="bot",
        last_message_at=expired_time,
        messaging_window_expires_at=expired_time,
        unread_count=0
    )

    account = InstagramAccount(
        id=account_id,
        tenant_id=tenant_id,
        ig_user_id="page_ig_id",
        page_id="page_123",
        username="test_page",
        encrypted_access_token=TokenEncryptor.encrypt_token("EAAB...valid_token"),
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    event = OutboxEvent(
        id=event_id,
        tenant_id=tenant_id,
        destination="meta_api",
        event_type="direct_message",
        idempotency_key="key_1",
        payload={
            "instagram_account_id": str(account_id),
            "recipient_id": "recipient_123",
            "text": "Salom! Bu avtomatik javob.",
            "conversation_id": str(conv_id)
        },
        status="sending",
        locked_by="worker-1"
    )

    with patch("app.repositories.outbox_repo.OutboxRepository.claim_pending_events", return_value=[event]), \
         patch("app.repositories.outbox_repo.OutboxRepository.mark_rejected_permanent", return_value=True) as mock_mark_perm:

        # Bazadan Account va Conversation qaytarish
        mock_session.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: account)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: conversation))
        ]

        await dispatcher.dispatch_batch(worker_id="worker-1", limit=1)

        # Meta API ga umuman so'rov bormasligi kerak
        mock_messaging_client.send_direct_message.assert_not_called()
        # Outbox rejected_permanent qilinishi kerak
        mock_mark_perm.assert_called_once()
        assert "24-hour" in mock_mark_perm.call_args[0][2]


@pytest.mark.asyncio
async def test_dispatcher_direct_message_success():
    """
    24 soatlik oyna faol bo'lsa, xabar Meta API ga jo'natiladi va
    accepted_by_meta holatiga o'tkaziladi.
    """
    mock_session = AsyncMock()
    mock_messaging_client = AsyncMock()
    mock_messaging_client.send_direct_message.return_value = {"message_id": "mid.12345"}

    dispatcher = OutboundDispatcher(mock_session, messaging_client=mock_messaging_client)

    tenant_id = uuid.uuid4()
    account_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    event_id = uuid.uuid4()

    valid_window = datetime.now(timezone.utc) + timedelta(hours=10)
    conversation = Conversation(
        id=conv_id,
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        ig_recipient_id="recipient_123",
        status="open",
        mode="bot",
        last_message_at=datetime.now(timezone.utc),
        messaging_window_expires_at=valid_window,
        unread_count=0
    )

    account = InstagramAccount(
        id=account_id,
        tenant_id=tenant_id,
        ig_user_id="page_ig_id",
        page_id="page_123",
        username="test_page",
        encrypted_access_token=TokenEncryptor.encrypt_token("EAAB...valid_token"),
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    event = OutboxEvent(
        id=event_id,
        tenant_id=tenant_id,
        destination="meta_api",
        event_type="direct_message",
        idempotency_key="key_2",
        payload={
            "instagram_account_id": str(account_id),
            "recipient_id": "recipient_123",
            "text": "Salom! Bu avtomatik javob.",
            "conversation_id": str(conv_id)
        },
        status="sending",
        locked_by="worker-1"
    )

    with patch("app.repositories.outbox_repo.OutboxRepository.claim_pending_events", return_value=[event]), \
         patch("app.repositories.outbox_repo.OutboxRepository.mark_accepted_by_meta", return_value=True) as mock_mark_accepted, \
         patch("app.repositories.message_repo.MessageRepository.save_message", return_value=MagicMock()):

        mock_session.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: account)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: conversation))
        ]

        count = await dispatcher.dispatch_batch(worker_id="worker-1", limit=1)

        assert count == 1
        mock_messaging_client.send_direct_message.assert_called_once_with(
            ig_user_id="page_ig_id",
            recipient_id="recipient_123",
            text="Salom! Bu avtomatik javob.",
            access_token="EAAB...valid_token"
        )
        mock_mark_accepted.assert_called_once_with(event_id, "worker-1")


@pytest.mark.asyncio
async def test_dispatcher_comment_private_reply_permanent_failure():
    """
    Meta 10900 xatolik (7 kundan eski yoki izoh o'chirilgan) qaytarsa:
    Outbox rejected_permanent, CommentLog failed_permanent bo'ladi.
    """
    mock_session = AsyncMock()
    mock_messaging_client = AsyncMock()
    mock_messaging_client.send_comment_private_reply.side_effect = MetaPermanentException(
        "Cannot message user because more than 7 days have passed", status_code=400, error_code=10900
    )

    dispatcher = OutboundDispatcher(mock_session, messaging_client=mock_messaging_client)

    tenant_id = uuid.uuid4()
    account_id = uuid.uuid4()
    comment_log_id = uuid.uuid4()
    event_id = uuid.uuid4()

    account = InstagramAccount(
        id=account_id,
        tenant_id=tenant_id,
        ig_user_id="page_ig_id",
        page_id="page_123",
        username="test_page",
        encrypted_access_token=TokenEncryptor.encrypt_token("EAAB...valid_token"),
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    comment = CommentLog(
        id=comment_log_id,
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        ig_comment_id="comment_789",
        ig_media_id="media_1",
        ig_user_id="user_1",
        comment_text="kurs",
        ig_comment_created_at=datetime.now(timezone.utc),
        private_reply_status="sending",
        private_reply_lease_version=2
    )

    event = OutboxEvent(
        id=event_id,
        tenant_id=tenant_id,
        destination="meta_api",
        event_type="comment_private_reply",
        idempotency_key="key_3",
        payload={
            "instagram_account_id": str(account_id),
            "comment_id": "comment_789",
            "text": "Private javob",
            "comment_log_id": str(comment_log_id)
        },
        status="sending",
        locked_by="worker-1"
    )

    with patch("app.repositories.outbox_repo.OutboxRepository.claim_pending_events", return_value=[event]), \
         patch("app.repositories.outbox_repo.OutboxRepository.mark_rejected_permanent", return_value=True) as mock_mark_outbox_perm, \
         patch("app.repositories.comment_repo.CommentRepository.claim_for_sending", return_value=comment), \
         patch("app.repositories.comment_repo.CommentRepository.mark_failed", return_value=True) as mock_mark_comment_failed:

        mock_session.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: account))
        ]

        await dispatcher.dispatch_batch(worker_id="worker-1", limit=1)

        mock_mark_outbox_perm.assert_called_once()
        mock_mark_comment_failed.assert_called_once()
        assert mock_mark_comment_failed.call_args[1]["is_permanent"] is True


@pytest.mark.asyncio
async def test_dispatcher_network_timeout_marks_unknown():
    """
    Architecture v2.5: Tarmoq timeouti yoki uzilishi holatida xabar
    'unknown' deb belgilanadi va to'g'ridan-to'g'ri qayta yuborilmaydi (duplication spam oldini olish).
    """
    mock_session = AsyncMock()
    mock_messaging_client = AsyncMock()
    mock_messaging_client.send_direct_message.side_effect = httpx.TimeoutException("Meta request timed out")

    dispatcher = OutboundDispatcher(mock_session, messaging_client=mock_messaging_client)

    tenant_id = uuid.uuid4()
    account_id = uuid.uuid4()
    conv_id = uuid.uuid4()
    event_id = uuid.uuid4()

    valid_window = datetime.now(timezone.utc) + timedelta(hours=10)
    conversation = Conversation(
        id=conv_id,
        tenant_id=tenant_id,
        instagram_account_id=account_id,
        ig_recipient_id="recipient_123",
        status="open",
        mode="bot",
        last_message_at=datetime.now(timezone.utc),
        messaging_window_expires_at=valid_window,
        unread_count=0
    )

    account = InstagramAccount(
        id=account_id,
        tenant_id=tenant_id,
        ig_user_id="page_ig_id",
        page_id="page_123",
        username="test_page",
        encrypted_access_token=TokenEncryptor.encrypt_token("EAAB...valid_token"),
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    event = OutboxEvent(
        id=event_id,
        tenant_id=tenant_id,
        destination="meta_api",
        event_type="direct_message",
        idempotency_key="key_4",
        payload={
            "instagram_account_id": str(account_id),
            "recipient_id": "recipient_123",
            "text": "Salom! Bu avtomatik javob.",
            "conversation_id": str(conv_id)
        },
        status="sending",
        locked_by="worker-1"
    )

    with patch("app.repositories.outbox_repo.OutboxRepository.claim_pending_events", return_value=[event]), \
         patch("app.repositories.outbox_repo.OutboxRepository.mark_unknown", return_value=True) as mock_mark_unknown:

        mock_session.execute.side_effect = [
            MagicMock(scalars=lambda: MagicMock(first=lambda: account)),
            MagicMock(scalars=lambda: MagicMock(first=lambda: conversation))
        ]

        await dispatcher.dispatch_batch(worker_id="worker-1", limit=1)

        mock_mark_unknown.assert_called_once()
        assert "Network timeout" in mock_mark_unknown.call_args[0][2]
