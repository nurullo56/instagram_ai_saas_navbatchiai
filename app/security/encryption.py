import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config.settings import settings


class TokenEncryptionService:
    """
    AES-256-GCM yordamida Meta Access Tokenlarini shifrlash va deshifrlash.
    Har bir shifrlash uchun yangi 12-baytli tasodifiy nonce hosil qilinadi va
    natija: base64(nonce + ciphertext + tag) ko'rinishida saqlanadi.
    """

    def __init__(self, key: str = settings.ENCRYPTION_KEY):
        # 32 bayt (256-bit) kalitni tayyorlash
        if len(key) == 64:  # Hex format
            self._key = bytes.fromhex(key)
        else:
            # Agar oddiy matn bo'lsa, 32 baytga keltiramiz
            self._key = key.encode("utf-8")[:32].ljust(32, b"0")
        self._aesgcm = AESGCM(self._key)

    def encrypt(self, plain_text: str) -> str:
        """Ochiq matnni shifrlash"""
        if not plain_text:
            return ""
        nonce = os.urandom(12)  # 96-bit nonce
        encrypted_bytes = self._aesgcm.encrypt(nonce, plain_text.encode("utf-8"), None)
        # Nonce + ciphertext ni birlashtirib base64 qilamiz
        return base64.b64encode(nonce + encrypted_bytes).decode("utf-8")

    def decrypt(self, encrypted_payload: str) -> str:
        """Shifrlangan matnni ochish"""
        if not encrypted_payload:
            return ""
        raw_data = base64.b64decode(encrypted_payload.encode("utf-8"))
        nonce = raw_data[:12]
        ciphertext = raw_data[12:]
        decrypted_bytes = self._aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode("utf-8")


token_encryption = TokenEncryptionService()


class TokenEncryptor:
    """Yordamchi statik interfeys"""
    @staticmethod
    def encrypt_token(plain_text: str) -> str:
        return token_encryption.encrypt(plain_text)

    @staticmethod
    def decrypt_token(encrypted_payload: str) -> str:
        return token_encryption.decrypt(encrypted_payload)

