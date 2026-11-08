import re
from typing import List, Dict, Any, Optional


class TriggerMatcher:
    """
    Kiruvchi xabarlar va izohlarni kalit so'z qoidalariga mosligini tekshiruvchi dvigatel.
    Qo'llab-quvvatlanadigan turlar: 'exact', 'contains', 'starts_with', 'regex'.
    """

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Matnni solishtirish uchun tozalash (kichik harflar, chetdagi bo'shliqlar)"""
        return (text or "").lower().strip()

    @classmethod
    def match(cls, text: str, trigger_config: Dict[str, Any]) -> bool:
        """
        Matn berilgan trigger konfiguratsiyasiga mos keladimi?
        trigger_config: {"keywords": ["narx", "kurs"], "match_type": "contains"}
        """
        normalized_text = cls._normalize_text(text)
        if not normalized_text:
            return False

        keywords: List[str] = trigger_config.get("keywords", [])
        match_type: str = trigger_config.get("match_type", "contains").lower()

        if not keywords and match_type != "all":
            return False

        if match_type == "all":
            # Har qanday xabar uchun (Default trigger)
            return True

        for kw in keywords:
            normalized_kw = cls._normalize_text(kw)
            if not normalized_kw:
                continue

            if match_type == "exact":
                if normalized_text == normalized_kw:
                    return True

            elif match_type == "contains":
                # Butun so'z yoki qism sifatida uchrashi
                if normalized_kw in normalized_text:
                    return True

            elif match_type == "starts_with":
                if normalized_text.startswith(normalized_kw):
                    return True

            elif match_type == "regex":
                try:
                    if re.search(kw, text, re.IGNORECASE):
                        return True
                except re.error:
                    continue

        return False
