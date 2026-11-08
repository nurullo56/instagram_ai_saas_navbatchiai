import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from app.models.instagram import InstagramAccount
from app.models.comment import CommentLog
from app.models.flow import FlowDefinition, FlowVersion
from app.services.comment_service import CommentService
from app.repositories.comment_repo import CommentRepository


@pytest.mark.asyncio
async def test_comment_older_than_7_days_is_skipped():
    """
    Architecture v2.5: Asl Instagram izohi 7 kundan eski bo'lsa,
    Meta API 10900 xatoligining oldini olish uchun Private Reply rad etiladi.
    """
    mock_session = AsyncMock()
    service = CommentService(mock_session)

    tenant_id = uuid.uuid4()
    account = InstagramAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        ig_user_id="ig_page_123",
        page_id="page_123",
        username="business_account",
        encrypted_access_token="enc_token",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    # 8 kun oldingi izoh
    created_at_8d_ago = datetime.now(timezone.utc) - timedelta(days=8)

    mock_comment = CommentLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        instagram_account_id=account.id,
        ig_comment_id="comment_old_1",
        ig_media_id="media_1",
        ig_user_id="user_1",
        comment_text="kurs narxi qancha?",
        ig_comment_created_at=created_at_8d_ago,
        private_reply_status="none",
        private_reply_lease_version=1
    )

    with patch.object(CommentRepository, "upsert_comment", return_value=mock_comment):
        result = await service.process_comment_event(
            tenant_id=tenant_id,
            instagram_account=account,
            ig_comment_id="comment_old_1",
            ig_media_id="media_1",
            ig_user_id="user_1",
            comment_text="kurs narxi qancha?",
            ig_comment_created_at=created_at_8d_ago
        )

    assert result["status"] == "skipped_expired_7d"
    assert "7 days" in result["reason"]


@pytest.mark.asyncio
async def test_comment_already_processed_is_not_duplicated():
    """
    Agar izohga Private Reply yuborilgan yoki yuborilmoqda bo'lsa,
    ikkinchi marta private reply navbatga qo'yilmaydi.
    """
    mock_session = AsyncMock()
    service = CommentService(mock_session)

    tenant_id = uuid.uuid4()
    account = InstagramAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        ig_user_id="ig_page_123",
        page_id="page_123",
        username="business_account",
        encrypted_access_token="enc_token",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    created_at = datetime.now(timezone.utc) - timedelta(hours=2)

    # Allaqachon yuborilgan izoh
    mock_comment = CommentLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        instagram_account_id=account.id,
        ig_comment_id="comment_sent_1",
        ig_media_id="media_1",
        ig_user_id="user_1",
        comment_text="narx",
        ig_comment_created_at=created_at,
        private_reply_status="sent",
        private_reply_lease_version=2
    )

    with patch.object(CommentRepository, "upsert_comment", return_value=mock_comment):
        result = await service.process_comment_event(
            tenant_id=tenant_id,
            instagram_account=account,
            ig_comment_id="comment_sent_1",
            ig_media_id="media_1",
            ig_user_id="user_1",
            comment_text="narx",
            ig_comment_created_at=created_at
        )

    assert result["status"] == "already_processed"
    assert result["private_reply_status"] == "sent"


@pytest.mark.asyncio
async def test_comment_trigger_match_and_enqueuing():
    """
    Yangi izoh kalit so'zga mos kelsa, Private Reply va Public Reply Outbox ga yoziladi.
    """
    mock_session = AsyncMock()
    service = CommentService(mock_session)

    tenant_id = uuid.uuid4()
    account = InstagramAccount(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        ig_user_id="ig_page_123",
        page_id="page_123",
        username="business_account",
        encrypted_access_token="enc_token",
        token_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        webhook_subscribed=True,
        is_active=True
    )

    created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
    mock_comment = CommentLog(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        instagram_account_id=account.id,
        ig_comment_id="comment_new_1",
        ig_media_id="media_1",
        ig_user_id="user_1",
        comment_text="kurs narxi qancha?",
        ig_comment_created_at=created_at,
        private_reply_status="none",
        private_reply_lease_version=1
    )

    flow_def = FlowDefinition(id=uuid.uuid4(), tenant_id=tenant_id, instagram_account_id=account.id, name="Narx Flow", is_active=True)
    flow_ver = FlowVersion(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        flow_definition_id=flow_def.id,
        version_number=1,
        trigger_type="comment_keyword",
        trigger_config={"keywords": ["narx"], "match_type": "contains"},
        nodes=[
            {
                "id": "node_1",
                "type": "comment_reply",
                "data": {
                    "private_reply_text": "Salom! Kurs narxi 500,000 so'm.",
                    "public_reply_text": "Direct orqali ma'lumot yubordik! 📩"
                }
            }
        ],
        edges=[],
        is_published=True
    )

    with patch.object(CommentRepository, "upsert_comment", return_value=mock_comment), \
         patch.object(CommentRepository, "queue_private_reply", return_value=True), \
         patch.object(service, "_find_matching_comment_flow", return_value=(flow_def, flow_ver)), \
         patch("app.repositories.outbox_repo.OutboxRepository.enqueue", return_value=MagicMock()):

        result = await service.process_comment_event(
            tenant_id=tenant_id,
            instagram_account=account,
            ig_comment_id="comment_new_1",
            ig_media_id="media_1",
            ig_user_id="user_1",
            comment_text="kurs narxi qancha?",
            ig_comment_created_at=created_at
        )

    assert result["status"] == "success"
    assert result["actions"]["private_reply"] == "enqueued"
    assert result["actions"]["public_reply"] == "enqueued"
