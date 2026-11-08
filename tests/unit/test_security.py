import uuid
import pytest
from app.security.password import hash_password, verify_password
from app.security.encryption import TokenEncryptionService
from app.security.jwt import create_access_token, create_refresh_token, decode_token
from app.security.tenant_context import set_current_tenant_id, get_current_tenant_id


def test_password_hashing():
    raw_password = "SuperSecretPassword123!"
    hashed = hash_password(raw_password)

    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_token_encryption_aes_gcm():
    service = TokenEncryptionService()
    token = "EAABwzLixnjYBO1234567890MetaTokenVeryLongAndSecret"

    encrypted = service.encrypt(token)
    assert encrypted != token
    assert len(encrypted) > 20

    decrypted = service.decrypt(encrypted)
    assert decrypted == token

    # Bo'sh matn tekshiruvi
    assert service.encrypt("") == ""
    assert service.decrypt("") == ""


def test_jwt_tokens():
    user_id = uuid.uuid4()
    tenant_id = uuid.uuid4()

    data = {"sub": str(user_id), "tenant_id": str(tenant_id)}
    access_token = create_access_token(data)
    assert isinstance(access_token, str)

    payload = decode_token(access_token)
    assert payload["sub"] == str(user_id)
    assert payload["tenant_id"] == str(tenant_id)
    assert payload["type"] == "access"

    refresh_token = create_refresh_token({"sub": str(user_id)})
    r_payload = decode_token(refresh_token)
    assert r_payload["sub"] == str(user_id)
    assert r_payload["type"] == "refresh"


def test_tenant_context():
    test_id = uuid.uuid4()
    set_current_tenant_id(test_id)
    assert get_current_tenant_id() == test_id

    set_current_tenant_id(None)
    assert get_current_tenant_id() is None
