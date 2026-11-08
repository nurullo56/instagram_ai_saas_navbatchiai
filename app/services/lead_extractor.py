import re
from typing import Dict, Any, Optional


class LeadExtractor:
    """
    Suhbat matnidan mijoz ma'lumotlarini (telefon, email, ism) ajratib oluvchi regex dvigateli.
    O'zbekiston (+998...) va xalqaro telefon raqamlarini tozalab standart formatga keltiradi.
    """

    # Telefon regex: +998901234567, 998901234567, +998 90 123 45 67, 901234567
    PHONE_REGEX = re.compile(
        r"(?:(?:\+?998[\s.-]?)?(?:\(?\d{2}\)?[\s.-]?)?\d{3}[\s.-]?\d{2}[\s.-]?\d{2}|\+?\d{10,15})"
    )

    # Email regex
    EMAIL_REGEX = re.compile(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    )

    # Ism ko'rsatish shablonlari
    NAME_PATTERNS = [
        re.compile(r"(?:mening\s+ismim|ismim|otim)\s+([A-ZА-ЯЁa-zа-яё']{2,25})", re.IGNORECASE),
        re.compile(r"(?:men|я)\s+([A-ZА-ЯЁa-zа-яё']{2,25})man", re.IGNORECASE)
    ]

    @classmethod
    def extract_phone(cls, text: str) -> Optional[str]:
        """Matndan telefon raqamini topish va tozalash"""
        if not text:
            return None
        match = cls.PHONE_REGEX.search(text)
        if not match:
            return None

        raw = match.group(0)
        digits = re.sub(r"\D", "", raw)

        # 9 ta raqam bo'lsa (901234567) -> 998901234567
        if len(digits) == 9:
            return f"+998{digits}"
        # 12 ta raqam va 998 bilan boshlansa -> +998...
        elif len(digits) == 12 and digits.startswith("998"):
            return f"+{digits}"
        elif len(digits) >= 10:
            return f"+{digits}"

        return None

    @classmethod
    def extract_email(cls, text: str) -> Optional[str]:
        """Matndan email manzilini topish"""
        if not text:
            return None
        match = cls.EMAIL_REGEX.search(text)
        return match.group(0).lower() if match else None

    @classmethod
    def extract_name(cls, text: str) -> Optional[str]:
        """Matndan mijoz ismini topish"""
        if not text:
            return None
        for pattern in cls.NAME_PATTERNS:
            match = pattern.search(text)
            if match:
                name = match.group(1).strip().capitalize()
                return name
        return None

    @classmethod
    def extract_all(cls, text: str) -> Dict[str, Optional[str]]:
        """Barcha mavjud kontakt ma'lumotlarini ajratib olish"""
        return {
            "phone_number": cls.extract_phone(text),
            "email": cls.extract_email(text),
            "full_name": cls.extract_name(text)
        }
