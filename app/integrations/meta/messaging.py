from typing import Dict, Any, Optional
from app.config.logging import logger
from app.integrations.meta.client import MetaGraphClient


class MetaMessagingClient:
    """
    Meta Graph API orqali xabarlarni jo'natish mijozi:
    - Direct Message jo'natish (/{ig_user_id}/messages)
    - Comment Private Reply jo'natish (/{comment_id}/messages)
    - Comment Public Reply jo'natish (/{comment_id}/replies)
    """

    def __init__(self, client: Optional[MetaGraphClient] = None):
        self.client = client or MetaGraphClient()

    async def send_direct_message(
        self,
        ig_user_id: str,
        recipient_id: str,
        text: str,
        access_token: str,
        quick_replies: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Direct xabar yuborish.
        Meta muvaffaqiyatli qabul qilganda: {"recipient_id": "...", "message_id": "mid.$..."} qaytaradi.
        """
        message_payload: Dict[str, Any] = {"text": text}
        if quick_replies:
            message_payload["quick_replies"] = quick_replies

        payload = {
            "recipient": {"id": recipient_id},
            "message": message_payload
        }

        logger.info("Meta Direct xabar yuborilmoqda", ig_user_id=ig_user_id, recipient_id=recipient_id)
        return await self.client.post(
            endpoint=f"{ig_user_id}/messages",
            json_data=payload,
            access_token=access_token
        )

    async def send_comment_private_reply(
        self,
        comment_id: str,
        text: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Post yoki Reels izohiga Private Reply (Direct) yuborish.
        Meta qoidasi: 7 kun ichida faqat 1 marta yuborish mumkin!
        """
        payload = {
            "recipient": {"comment_id": comment_id},
            "message": {"text": text}
        }

        logger.info("Meta Comment Private Reply yuborilmoqda", comment_id=comment_id)
        return await self.client.post(
            endpoint=f"{comment_id}/messages",
            json_data=payload,
            access_token=access_token
        )

    async def send_comment_public_reply(
        self,
        comment_id: str,
        text: str,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Post yoki Reels izohi ostiga ommaviy javob qaytarish.
        """
        payload = {
            "message": text
        }

        logger.info("Meta Comment Public Reply yuborilmoqda", comment_id=comment_id)
        return await self.client.post(
            endpoint=f"{comment_id}/replies",
            json_data=payload,
            access_token=access_token
        )
