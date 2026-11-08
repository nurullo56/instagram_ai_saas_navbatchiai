import pytest
from app.services.trigger_matcher import TriggerMatcher


def test_trigger_matcher_exact():
    config = {"keywords": ["narx", "kurs"], "match_type": "exact"}

    assert TriggerMatcher.match("narx", config) is True
    assert TriggerMatcher.match("  NARX  ", config) is True
    assert TriggerMatcher.match("kurs", config) is True
    assert TriggerMatcher.match("kurs narxi qancha?", config) is False


def test_trigger_matcher_contains():
    config = {"keywords": ["narx", "kurs"], "match_type": "contains"}

    assert TriggerMatcher.match("Salom, kurs narxi qancha?", config) is True
    assert TriggerMatcher.match("KURS haqida ma'lumot bering", config) is True
    assert TriggerMatcher.match("Hech narsa yo'q", config) is False


def test_trigger_matcher_starts_with():
    config = {"keywords": ["start", "/boshlash"], "match_type": "starts_with"}

    assert TriggerMatcher.match("start men tayyorman", config) is True
    assert TriggerMatcher.match("/boshlash", config) is True
    assert TriggerMatcher.match("men start bosdim", config) is False


def test_trigger_matcher_regex():
    config = {"keywords": [r"^\d{9}$", r"order_\d+"], "match_type": "regex"}

    assert TriggerMatcher.match("998901234", config) is True
    assert TriggerMatcher.match("order_48291", config) is True
    assert TriggerMatcher.match("order_abc", config) is False


def test_trigger_matcher_all():
    config = {"keywords": [], "match_type": "all"}

    assert TriggerMatcher.match("Har qanday xabar", config) is True
    assert TriggerMatcher.match("123", config) is True


def test_trigger_matcher_empty_and_invalid():
    assert TriggerMatcher.match("", {"keywords": ["test"], "match_type": "contains"}) is False
    assert TriggerMatcher.match("salom", {"keywords": [], "match_type": "contains"}) is False
    # Noto'g'ri regex regex xatosiga olib kelmasligi kerak
    assert TriggerMatcher.match("test", {"keywords": ["[invalid"], "match_type": "regex"}) is False
