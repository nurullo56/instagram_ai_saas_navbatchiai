from typing import Optional, Dict, Any


class MetaAPIException(Exception):
    """Barcha Meta Graph API xatoliklari uchun asosiy sinf"""
    def __init__(self, message: str, status_code: int = 400, error_code: Optional[int] = None, error_subcode: Optional[int] = None, raw_response: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.error_subcode = error_subcode
        self.raw_response = raw_response or {}


class MetaRateLimitException(MetaAPIException):
    """Meta so'rovlar limiti tugagan (Error Code: 4, 17, 32, 613 yoki HTTP 429)"""
    pass


class MetaAuthException(MetaAPIException):
    """OAuth token eskirgan yoki ruxsat bekor qilingan (Error Code: 190)"""
    pass


class MetaMessagingWindowException(MetaAPIException):
    """24-soatlik standart xabarlar oynasi tugagan (Error Code: 10 / Subcode: 2018028)"""
    pass


class MetaPermanentException(MetaAPIException):
    """Qayta urinish befoyda bo'lgan doimiy xatolik (noto'g'ri parametr, bloklangan foydalanuvchi)"""
    pass


class MetaNetworkTimeoutException(MetaAPIException):
    """Tarmoq uzilishi yoki Meta serveridan javob kechikishi (Timeout)"""
    pass


def classify_meta_error(status_code: int, response_json: Dict[str, Any]) -> MetaAPIException:
    """Meta Graph API javobidagi xatolik kodi va subkodini toifalash"""
    error_data = response_json.get("error", {})
    message = error_data.get("message", "Noma'lum Meta API xatoligi")
    code = error_data.get("code")
    subcode = error_data.get("error_subcode")

    # 1. Rate Limit
    if status_code == 429 or code in (4, 17, 32, 613):
        return MetaRateLimitException(message, status_code, code, subcode, response_json)

    # 2. Token muddati o'tgan / bekor qilingan
    if code == 190 or subcode in (463, 467):
        return MetaAuthException(message, status_code, code, subcode, response_json)

    # 3. 24-soatlik oyna cheklovi
    if code == 10 and subcode == 2018028:
        return MetaMessagingWindowException(message, status_code, code, subcode, response_json)

    # 4. Server xatolari (5xx)
    if status_code >= 500:
        return MetaAPIException(f"Meta server xatosi: {message}", status_code, code, subcode, response_json)

    # 5. Doimiy mijoz xatolari
    return MetaPermanentException(message, status_code, code, subcode, response_json)
