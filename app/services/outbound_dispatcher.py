import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.logging import logger
from app.models.instagram import InstagramAccount
from app.models.conversation import Conversation
from app.models.comment import CommentLog
from app.models.outbox import OutboxEvent
from app.repositories.outbox_repo import OutboxRepository
from app.repositories.comment_repo import CommentRepository
from app.repositories.conversation_repo import ConversationRepository
from app.repositories.message_repo import MessageRepository
from app.security.encryption import TokenEncryptor
from app.integrations.meta.messaging import MetaMessagingClient
from app.integrations.meta.exceptions import (
    MetaAPIException,
    MetaRateLimitException,
    MetaAuthException,
    MetaMessagingWindowException,
    MetaPermanentException,
    MetaNetworkTimeoutException,
)


class OutboundDispatcher:
    """
    Transactional Outbox navbatidagi xabarlarni Meta Graph API ga xavfsiz yetkazish dvigateli.
    - 24-soatlik Direct Messaging oynasini qat'iy tekshirish
    - Comment Private Reply 7-kunlik cheklovi va 5-holatli atomik lease himoyasi
    - Meta API javobiga qarab statuslarni to'g'ri yangilash (accepted_by_meta, rejected_transient, rejected_permanent, unknown)
    - Tokenni AES-256-GCM orqali deshifrlash
    """

    def __init__(
        self,
        session: AsyncSession,
        messaging_client: Optional[MetaMessagingClient] = None
    ):
        self.session = session
        self.client = messaging_client or MetaMessagingClient()

    async def dispatch_batch(self, worker_id: str, limit: int = 10) -> int:
        """
        Navbatdagi xabarlar paketini egallash va Meta API ga jo'natish.
        Qaytaradi: muvaffaqiyatli jo'natilgan xabarlar soni.
        """
        outbox_repo = OutboxRepository(self.session)
        claimed_events = await outbox_repo.claim_pending_events(worker_id=worker_id, limit=limit)

        if not claimed_events:
            return 0

        success_count = 0
        for event in claimed_events:
            event_id = event.id
            tenant_id = event.tenant_id
            payload = event.payload or {}
            event_type = event.event_type

            try:
                # 1. Instagram akkauntni topish va tokenni deshifrlash
                account_id_str = payload.get("instagram_account_id")
                if not account_id_str:
                    await outbox_repo.mark_rejected_permanent(
                        event_id, worker_id, "Missing instagram_account_id in outbox payload"
                    )
                    continue

                account_id = uuid.UUID(account_id_str)
                stmt = select(InstagramAccount).where(
                    InstagramAccount.tenant_id == tenant_id,
                    InstagramAccount.id == account_id
                )
                res = await self.session.execute(stmt)
                account = res.scalars().first()

                if not account or not account.is_active:
                    await outbox_repo.mark_rejected_permanent(
                        event_id, worker_id, f"Instagram account {account_id} not found or inactive"
                    )
                    continue

                access_token = TokenEncryptor.decrypt_token(account.encrypted_access_token)

                # 2. Xabar turiga qarab jo'natish
                if event_type == "direct_message":
                    await self._dispatch_direct_message(
                        event_id=event_id,
                        tenant_id=tenant_id,
                        account=account,
                        access_token=access_token,
                        payload=payload,
                        worker_id=worker_id,
                        outbox_repo=outbox_repo
                    )
                    success_count += 1

                elif event_type == "comment_private_reply":
                    await self._dispatch_comment_private_reply(
                        event_id=event_id,
                        tenant_id=tenant_id,
                        account=account,
                        access_token=access_token,
                        payload=payload,
                        worker_id=worker_id,
                        outbox_repo=outbox_repo
                    )
                    success_count += 1

                elif event_type == "comment_public_reply":
                    await self._dispatch_comment_public_reply(
                        event_id=event_id,
                        tenant_id=tenant_id,
                        access_token=access_token,
                        payload=payload,
                        worker_id=worker_id,
                        outbox_repo=outbox_repo
                    )
                    success_count += 1

                else:
                    await outbox_repo.mark_rejected_permanent(
                        event_id, worker_id, f"Unknown outbox event type: {event_type}"
                    )

            except Exception as e:
                logger.error(
                    "Outbox xabarini jo'natishda kutilmagan xatolik",
                    event_id=str(event_id),
                    event_type=event_type,
                    error=str(e)
                )
                await outbox_repo.mark_rejected_transient(
                    event_id, worker_id, f"Unexpected error: {str(e)}"
                )

        await self.session.commit()
        return success_count

    async def _dispatch_direct_message(
        self,
        event_id: uuid.UUID,
        tenant_id: uuid.UUID,
        account: InstagramAccount,
        access_token: str,
        payload: Dict[str, Any],
        worker_id: str,
        outbox_repo: OutboxRepository
    ) -> None:
        """Direct xabarni Meta Send API orqali jo'natish"""
        recipient_id = payload["recipient_id"]
        text_content = payload["text"]
        conversation_id_str = payload.get("conversation_id")

        # 24-soatlik oynani tekshirish
        if conversation_id_str:
            conv_id = uuid.UUID(conversation_id_str)
            conv_repo = ConversationRepository(self.session, tenant_id=tenant_id)
            stmt = select(Conversation).where(
                Conversation.tenant_id == tenant_id,
                Conversation.id == conv_id
            )
            conv = (await self.session.execute(stmt)).scalars().first()

            if conv:
                now = datetime.now(timezone.utc)
                if conv.messaging_window_expires_at < now:
                    logger.warning(
                        "Direct xabar yuborish rad etildi: 24 soatlik Meta oynasi tugagan",
                        tenant_id=str(tenant_id),
                        conversation_id=str(conv_id)
                    )
                    await outbox_repo.mark_rejected_permanent(
                        event_id, worker_id, "24-hour Meta messaging window has expired"
                    )
                    return

        try:
            resp = await self.client.send_direct_message(
                ig_user_id=account.ig_user_id,
                recipient_id=recipient_id,
                text=text_content,
                access_token=access_token
            )
            await outbox_repo.mark_accepted_by_meta(event_id, worker_id)

            # Xabarlar bazasiga bot javobini saqlash
            if conversation_id_str:
                msg_repo = MessageRepository(self.session, tenant_id=tenant_id)
                await msg_repo.save_message(
                    tenant_id=tenant_id,
                    conversation_id=uuid.UUID(conversation_id_str),
                    mid=resp.get("message_id"),
                    sender_type="bot",
                    message_text=text_content,
                    status="sent"
                )

        except MetaMessagingWindowException as e:
            await outbox_repo.mark_rejected_permanent(event_id, worker_id, f"24h window closed: {str(e)}")
        except MetaRateLimitException as e:
            await outbox_repo.mark_rejected_transient(event_id, worker_id, f"Rate limited: {str(e)}")
        except (MetaNetworkTimeoutException, httpx.TimeoutException) as e:
            await outbox_repo.mark_unknown(event_id, worker_id, f"Network timeout: {str(e)}")
        except MetaPermanentException as e:
            await outbox_repo.mark_rejected_permanent(event_id, worker_id, f"Permanent error: {str(e)}")
        except MetaAPIException as e:
            await outbox_repo.mark_rejected_transient(event_id, worker_id, f"Meta API transient error: {str(e)}")

    async def _dispatch_comment_private_reply(
        self,
        event_id: uuid.UUID,
        tenant_id: uuid.UUID,
        account: InstagramAccount,
        access_token: str,
        payload: Dict[str, Any],
        worker_id: str,
        outbox_repo: OutboxRepository
    ) -> None:
        """Comment Private Reply ni Meta Send API orqali jo'natish"""
        comment_id = payload["comment_id"]
        text_content = payload["text"]
        comment_log_id_str = payload.get("comment_log_id")

        comment_repo = CommentRepository(self.session, tenant_id=tenant_id)
        comment_log_id = uuid.UUID(comment_log_id_str) if comment_log_id_str else None

        # Izoh yozuvini sending holatiga lock qilish (lease version himoyasi bilan)
        claimed_comment = None
        if comment_log_id:
            claimed_comment = await comment_repo.claim_for_sending(
                tenant_id=tenant_id,
                comment_id=comment_log_id,
                worker_id=worker_id
            )
            if not claimed_comment:
                # Boshqa worker allaqachon yuborgan yoki lock olgan
                logger.info(
                    "Comment private reply lock olib bo'lmadi (boshqa worker jo'natmoqda yoki yuborilgan)",
                    comment_log_id=comment_log_id_str
                )
                await outbox_repo.mark_rejected_permanent(
                    event_id, worker_id, "Could not acquire comment private reply lease"
                )
                return

        lease_version = claimed_comment.private_reply_lease_version if claimed_comment else 1

        try:
            resp = await self.client.send_comment_private_reply(
                comment_id=comment_id,
                text=text_content,
                access_token=access_token
            )
            await outbox_repo.mark_accepted_by_meta(event_id, worker_id)
            if comment_log_id:
                await comment_repo.mark_sent(
                    tenant_id=tenant_id,
                    comment_id=comment_log_id,
                    worker_id=worker_id,
                    lease_version=lease_version,
                    reply_text=text_content
                )

        except MetaPermanentException as e:
            err_msg = str(e)
            await outbox_repo.mark_rejected_permanent(event_id, worker_id, f"Permanent error: {err_msg}")
            if comment_log_id:
                await comment_repo.mark_failed(
                    tenant_id=tenant_id,
                    comment_id=comment_log_id,
                    worker_id=worker_id,
                    lease_version=lease_version,
                    error_message=err_msg,
                    is_permanent=True
                )
        except (MetaNetworkTimeoutException, httpx.TimeoutException) as e:
            err_msg = str(e)
            await outbox_repo.mark_unknown(event_id, worker_id, f"Network timeout: {err_msg}")
            if comment_log_id:
                await comment_repo.mark_unknown(
                    tenant_id=tenant_id,
                    comment_id=comment_log_id,
                    worker_id=worker_id,
                    lease_version=lease_version,
                    error_message=err_msg
                )
        except MetaRateLimitException as e:
            err_msg = str(e)
            await outbox_repo.mark_rejected_transient(event_id, worker_id, f"Rate limited: {err_msg}")
            if comment_log_id:
                await comment_repo.mark_failed(
                    tenant_id=tenant_id,
                    comment_id=comment_log_id,
                    worker_id=worker_id,
                    lease_version=lease_version,
                    error_message=err_msg,
                    is_permanent=False
                )
        except MetaAPIException as e:
            err_msg = str(e)
            await outbox_repo.mark_rejected_transient(event_id, worker_id, f"Transient error: {err_msg}")
            if comment_log_id:
                await comment_repo.mark_failed(
                    tenant_id=tenant_id,
                    comment_id=comment_log_id,
                    worker_id=worker_id,
                    lease_version=lease_version,
                    error_message=err_msg,
                    is_permanent=False
                )

    async def _dispatch_comment_public_reply(
        self,
        event_id: uuid.UUID,
        tenant_id: uuid.UUID,
        access_token: str,
        payload: Dict[str, Any],
        worker_id: str,
        outbox_repo: OutboxRepository
    ) -> None:
        """Comment Public Reply ni Meta Graph API orqali jo'natish"""
        comment_id = payload["comment_id"]
        text_content = payload["text"]

        try:
            await self.client.send_comment_public_reply(
                comment_id=comment_id,
                text=text_content,
                access_token=access_token
            )
            await outbox_repo.mark_accepted_by_meta(event_id, worker_id)

        except MetaPermanentException as e:
            await outbox_repo.mark_rejected_permanent(event_id, worker_id, f"Permanent error: {str(e)}")
        except (MetaNetworkTimeoutException, httpx.TimeoutException) as e:
            await outbox_repo.mark_unknown(event_id, worker_id, f"Network timeout: {str(e)}")
        except MetaAPIException as e:
            await outbox_repo.mark_rejected_transient(event_id, worker_id, f"Transient error: {str(e)}")
