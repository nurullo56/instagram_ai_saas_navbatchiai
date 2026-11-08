import pytest
from app.services.lead_extractor import LeadExtractor


def test_lead_extractor_phone_numbers():
    # 9 raqamli format
    assert LeadExtractor.extract_phone("Mening raqamim 901234567") == "+998901234567"
    # To'liq +998 format
    assert LeadExtractor.extract_phone("Aloqa uchun: +998935556677 yozing") == "+998935556677"
    # Bo'shliqlar bilan
    assert LeadExtractor.extract_phone("Tel: +998 97 111 22 33") == "+998971112233"
    # Raqam bo'lmaganda
    assert LeadExtractor.extract_phone("Menga xabar yozing") is None


def test_lead_extractor_emails():
    assert LeadExtractor.extract_email("Emailim: user.test@gmail.com") == "user.test@gmail.com"
    assert LeadExtractor.extract_email("Aloqa: INFO@COMPANY.UZ") == "info@company.uz"
    assert LeadExtractor.extract_email("Emailim yo'q") is None


def test_lead_extractor_names():
    assert LeadExtractor.extract_name("Mening ismim Ali, kurs haqida ma'lumot bering") == "Ali"
    assert LeadExtractor.extract_name("Ismim Jasur") == "Jasur"
    assert LeadExtractor.extract_name("Salom qalesiz") is None


def test_lead_extractor_extract_all():
    text = "Salom! Mening ismim Nodir, raqamim 901234567, pochtam nodir@mail.ru"
    extracted = LeadExtractor.extract_all(text)

    assert extracted["full_name"] == "Nodir"
    assert extracted["phone_number"] == "+998901234567"
    assert extracted["email"] == "nodir@mail.ru"
