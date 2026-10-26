"""Every message key exists in all 3 languages; every placeholder is filled."""

from string import Formatter

from src.messages import DATA_QUALITY_KEYS, LANGUAGES, MESSAGES, REASON_KEYS, render_alert


def placeholders(template: str) -> set:
    """Return the {names} used in a template, e.g. {"bed", "risk"}."""
    return {name for _, name, _, _ in Formatter().parse(template) if name}


def test_every_language_has_the_same_keys():
    for lang in LANGUAGES:
        assert set(MESSAGES[lang]) == set(MESSAGES["en"]), f"{lang} has different keys"


def test_every_message_is_written():
    for lang in LANGUAGES:
        missing = [key for key, value in MESSAGES[lang].items() if not value]
        assert not missing, f"{lang}: still to write: {missing}"


def test_placeholders_match_english():
    for lang in LANGUAGES:
        for key, template in MESSAGES[lang].items():
            if template:
                assert placeholders(template) == placeholders(MESSAGES["en"][key]), f"{lang}/{key}"


def test_render_alert_fills_everything():
    items = [(key, {"value": "14"}) for key in REASON_KEYS] + [
        ("lactate_stale", {"hours": "7"}), ("lactate_never", {}), ("trends_not_ready", {})]
    for lang in LANGUAGES:
        alert = render_alert(12, 8.4, items, lang)
        assert "{" not in alert and "}" not in alert
        assert "12" in alert and "8.4" in alert


def test_render_alert_without_reasons_says_so():
    alert = render_alert(3, 2.0, [], "en")
    assert "No worsening sign right now" in alert
    assert "not a diagnosis" in alert


def test_reason_and_note_keys_exist():
    for key in REASON_KEYS + DATA_QUALITY_KEYS:
        assert key in MESSAGES["en"]
