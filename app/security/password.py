from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

_ph = PasswordHasher()


def hash_password(password: str) -> str:
    """Parolni Argon2id algoritmi yordamida heshlash"""
    return _ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Parolning to'g'riligini tekshirish"""
    try:
        return _ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
