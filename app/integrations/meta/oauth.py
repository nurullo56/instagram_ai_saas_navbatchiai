import urllib.parse
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, timezone
from app.config.settings import settings
from app.config.logging import logger
from app.integrations.meta.client import MetaGraphClient


class MetaOAuthService:
    """
    Facebook Login for Business OAuth 2.0 oqimi.
    Instagram Professional akkauntlarini Facebook Sahifalar orqali ulash,
    tokenlarni 60-kunlik Long-Lived tokenga aylantirish va Webhooklarga obuna qilish.
    """

    OFFICIAL_SCOPES = [
        "pages_show_list",
        "pages_read_engagement",
        "pages_manage_metadata",
        "instagram_basic",
        "instagram_manage_messages",
        "instagram_manage_comments",
    ]

    def __init__(self, client: Optional[MetaGraphClient] = None):
        self.client = client or MetaGraphClient()

    def get_authorization_url(self, redirect_uri: str, state: str) -> str:
        """Mijozni Facebook OAuth oynasiga yo'naltiruvchi URL ni hosil qilish"""
        base_url = f"https://www.facebook.com/{settings.META_GRAPH_API_VERSION}/dialog/oauth"
        params = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": ",".join(self.OFFICIAL_SCOPES),
            "response_type": "code",
        }
        return f"{base_url}?{urllib.parse.urlencode(params)}"

    async def exchange_code_for_short_lived_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """OAuth kodi (code) orqali Short-Lived User Token (~2 soatlik) olish"""
        params = {
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "redirect_uri": redirect_uri,
            "code": code,
        }
        data = await self.client.get("oauth/access_token", params=params)
        logger.info("Short-lived token muvaffaqiyatli olindi")
        return data

    async def exchange_for_long_lived_token(self, short_lived_token: str) -> Dict[str, Any]:
        """Short-Lived User Tokenni 60-kunlik Long-Lived Tokenga aylantirish"""
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": settings.META_APP_ID,
            "client_secret": settings.META_APP_SECRET,
            "fb_exchange_token": short_lived_token,
        }
        data = await self.client.get("oauth/access_token", params=params)
        logger.info("Long-lived 60-kunlik token muvaffaqiyatli olindi")
        return data

    async def get_managed_pages_and_instagram_accounts(self, user_access_token: str) -> List[Dict[str, Any]]:
        """
        Foydalanuvchiga tegishli Facebook sahifalar va ularga bog'langan
        Instagram Business akkauntlarni olish.
        """
        params = {
            "fields": "id,name,access_token,instagram_business_account{id,username,name,profile_picture_url}"
        }
        data = await self.client.get("me/accounts", params=params, access_token=user_access_token)
        pages = data.get("data", [])
        connected_accounts = []

        for page in pages:
            ig_account = page.get("instagram_business_account")
            if ig_account and "id" in ig_account:
                connected_accounts.append({
                    "page_id": page["id"],
                    "page_name": page.get("name"),
                    "page_access_token": page["access_token"],
                    "ig_user_id": ig_account["id"],
                    "ig_username": ig_account.get("username"),
                    "ig_name": ig_account.get("name"),
                    "ig_profile_picture_url": ig_account.get("profile_picture_url"),
                })

        logger.info("Bog'langan Instagram akkauntlar aniqlandi", count=len(connected_accounts))
        return connected_accounts

    async def subscribe_page_to_webhooks(self, page_id: str, page_access_token: str) -> bool:
        """
        Sahifaga bizning ilovamiz nomidan Webhook hodisalariga (xabarlar, izohlar) obunani faollashtirish.
        """
        params = {
            "subscribed_fields": "messages,messaging_postbacks,messaging_seen,comments"
        }
        res = await self.client.post(f"{page_id}/subscribed_apps", params=params, access_token=page_access_token)
        success = res.get("success", False)
        logger.info("Sahifa webhooklarga obuna qilindi", page_id=page_id, success=success)
        return success
