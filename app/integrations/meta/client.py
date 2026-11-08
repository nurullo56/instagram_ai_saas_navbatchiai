from typing import Dict, Any, Optional
import httpx
from app.config.settings import settings
from app.config.logging import logger
from app.integrations.meta.exceptions import classify_meta_error, MetaNetworkTimeoutException, MetaAPIException


class MetaGraphClient:
    """
    Meta Graph API v21.0 bilan asinxron ishlovchi asosiy HTTP mijoz.
    Barcha so'rovlar configurable endpoint orqali yuboriladi va
    xatoliklar avtomatik toifalanadi.
    """

    def __init__(self, base_url: Optional[str] = None, timeout: float = 15.0):
        self.base_url = (base_url or settings.meta_api_endpoint).rstrip("/")
        self.timeout = timeout

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        params = params or {}
        if access_token:
            params["access_token"] = access_token

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json_data
                )
            except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout) as e:
                logger.error("Meta API tarmoq timeouti", endpoint=endpoint, error=str(e))
                raise MetaNetworkTimeoutException(f"Meta serveriga ulanishda timeout yuz berdi: {str(e)}")
            except httpx.RequestError as e:
                logger.error("Meta API tarmoq xatosi", endpoint=endpoint, error=str(e))
                raise MetaAPIException(f"Meta serveriga ulanishda xato: {str(e)}")

            if not response.is_success:
                try:
                    error_json = response.json()
                except Exception:
                    error_json = {"error": {"message": response.text}}
                logger.warning(
                    "Meta API xatolik qaytardi",
                    status_code=response.status_code,
                    endpoint=endpoint,
                    error=error_json
                )
                raise classify_meta_error(response.status_code, error_json)

            try:
                return response.json()
            except Exception:
                return {"success": True}

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None, access_token: Optional[str] = None) -> Dict[str, Any]:
        return await self._request("GET", endpoint, params=params, access_token=access_token)

    async def post(self, endpoint: str, json_data: Optional[Dict[str, Any]] = None, params: Optional[Dict[str, Any]] = None, access_token: Optional[str] = None) -> Dict[str, Any]:
        return await self._request("POST", endpoint, params=params, json_data=json_data, access_token=access_token)

    async def delete(self, endpoint: str, params: Optional[Dict[str, Any]] = None, access_token: Optional[str] = None) -> Dict[str, Any]:
        return await self._request("DELETE", endpoint, params=params, access_token=access_token)
