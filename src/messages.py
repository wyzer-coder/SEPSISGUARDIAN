"""English, Tamil and Hindi message templates (fixed text, no live translation).

Every language has the SAME keys. Words in {curly brackets} are filled in by the code:
  {bed} bed number · {risk} risk in % · {value} a measurement · {hours} hours
Keep the {curly bracket} words exactly as they are when translating.

Tamil: written by the student.  Hindi: drafted by Claude, reviewed by the student.
"""

from typing import Dict, List, Optional, Tuple

LANGUAGES = ["en", "ta", "hi"]
LANGUAGE_NAMES = {"en": "English", "ta": "தமிழ்", "hi": "हिन्दी"}

MESSAGES: Dict[str, Dict[str, Optional[str]]] = {
    "en": {
        # Status names
        "status_NO_ALERT": "No alert",
        "status_WATCH": "Watch",
        "status_SUPPRESSED": "Suppressed (alerted recently)",
        "status_REVIEW": "Review now",
        # Alert headline and section titles
        "alert_headline": "Bed {bed}: sepsis risk {risk}%. Please review the patient now.",
        "why_now_title": "Why now",
        "data_quality_title": "Data quality",
        "no_reason": "No worsening sign right now",
        # Reasons
        "map_fell": "MAP fell by {value} mmHg in the last 3 hours",
        "hr_rose": "Heart rate rose by {value} bpm in the last 3 hours",
        "lactate_rose": "Lactate rose by {value} mmol/L in the last 3 hours",
        "resp_high": "Breathing rate is {value} per minute",
        "o2_low": "Oxygen saturation is {value}%",
        # Data-quality notes
        "lactate_stale": "Lactate not measured for {hours} hours, so confidence is lower",
        "lactate_never": "Lactate not measured yet, so confidence is lower",
        "trends_not_ready": "Less than 3 hours of data, so trends are not available yet",
        # Safety
        "safety_line": "Clinical decision support — not a diagnosis. A clinician must confirm.",
    },
    "ta": {
        # Written by the student (23 Oct 2026); placeholders {bed} {risk} {value} {hours} re-inserted by Claude.
        "status_NO_ALERT": "எச்சரிக்கை இல்லை",       # No alert
        "status_WATCH": "கண்காணிக்கவும்",          # Watch
        "status_SUPPRESSED": "சமீபத்தில் எச்சரிக்கை வழங்கப்பட்டதால், தற்போதைய எச்சரிக்கை தற்காலிகமாகத் தடுக்கப்பட்டுள்ளது",     # Suppressed (alerted recently)
        "status_REVIEW": "இப்போதே மதிப்பாய்வு செய்யவும்",         # Review now
        "alert_headline": "படுக்கை {bed}: செப்சிஸ் ஏற்படும் அபாயம் {risk}%. நோயாளியை இப்போதே மதிப்பாய்வு செய்யவும்.",        # Bed {bed}: sepsis risk {risk}%. Please review the patient now.
        "why_now_title": "இப்போது ஏன் எச்சரிக்கை வழங்கப்படுகிறது?",         # Why now
        "data_quality_title": "தரவின் தரம்",    # Data quality
        "no_reason": "தற்போதைக்கு உடல்நிலை மோசமடைவதற்கான அறிகுறிகள் இல்லை",             # No worsening sign right now
        "map_fell": "கடந்த 3 மணி நேரத்தில் சராசரி தமனி இரத்த அழுத்தம் (MAP) {value} mmHg குறைந்துள்ளது",              # MAP fell by {value} mmHg in the last 3 hours
        "hr_rose": "கடந்த 3 மணி நேரத்தில் இதயத் துடிப்பு நிமிடத்திற்கு {value} துடிப்புகள் அதிகரித்துள்ளன",               # Heart rate rose by {value} bpm in the last 3 hours
        "lactate_rose": "கடந்த 3 மணி நேரத்தில் லாக்டேட் அளவு {value} mmol/L அதிகரித்துள்ளது",          # Lactate rose by {value} mmol/L in the last 3 hours
        "resp_high": "சுவாச வீதம் நிமிடத்திற்கு {value} ஆக உள்ளது",             # Breathing rate is {value} per minute
        "o2_low": "இரத்தத்தில் ஆக்சிஜன் செறிவு {value}% ஆக உள்ளது",                # Oxygen saturation is {value}%
        "lactate_stale": "கடந்த {hours} மணி நேரமாக லாக்டேட் அளவு அளவிடப்படவில்லை. எனவே, மதிப்பீட்டின் நம்பகத்தன்மை குறைவாக உள்ளது",         # Lactate not measured for {hours} hours, so confidence is lower
        "lactate_never": "லாக்டேட் அளவு இதுவரை அளவிடப்படவில்லை. எனவே, மதிப்பீட்டின் நம்பகத்தன்மை குறைவாக உள்ளது",         # Lactate not measured yet, so confidence is lower
        "trends_not_ready": "3 மணி நேரத்திற்கும் குறைவான தரவுகளே உள்ளன. எனவே, மாற்றங்களின் போக்கை இன்னும் மதிப்பிட முடியவில்லை",      # Less than 3 hours of data, so trends are not available yet
        "safety_line": "மருத்துவ முடிவெடுப்பதற்கான ஆதரவு மட்டுமே — இது நோயறிதல் அல்ல. மருத்துவ நிபுணர் இதை உறுதிப்படுத்த வேண்டும்.",           # Clinical decision support — not a diagnosis. A clinician must confirm.
    },
    "hi": {
        # Draft by Claude — the student reviews it.
        "status_NO_ALERT": "कोई अलर्ट नहीं",
        "status_WATCH": "निगरानी रखें",
        "status_SUPPRESSED": "रोका गया (हाल ही में अलर्ट दिया गया)",
        "status_REVIEW": "अभी जाँच करें",
        "alert_headline": "बेड {bed}: सेप्सिस जोखिम {risk}%। कृपया अभी मरीज़ की जाँच करें।",
        "why_now_title": "अभी क्यों",
        "data_quality_title": "डेटा की गुणवत्ता",
        "no_reason": "अभी बिगड़ने का कोई संकेत नहीं",
        "map_fell": "पिछले 3 घंटों में MAP {value} mmHg गिरा",
        "hr_rose": "पिछले 3 घंटों में हृदय गति {value} bpm बढ़ी",
        "lactate_rose": "पिछले 3 घंटों में लैक्टेट {value} mmol/L बढ़ा",
        "resp_high": "साँस की दर {value} प्रति मिनट है",
        "o2_low": "ऑक्सीजन सैचुरेशन {value}% है",
        "lactate_stale": "लैक्टेट {hours} घंटों से नहीं मापा गया, इसलिए भरोसा कम है",
        "lactate_never": "लैक्टेट अभी तक नहीं मापा गया, इसलिए भरोसा कम है",
        "trends_not_ready": "3 घंटे से कम डेटा है, इसलिए रुझान अभी उपलब्ध नहीं हैं",
        "safety_line": "क्लिनिकल निर्णय सहायता — यह निदान नहीं है। क्लिनिशियन को पुष्टि करनी होगी।",
    },
}

REASON_KEYS = ["map_fell", "hr_rose", "lactate_rose", "resp_high", "o2_low"]
DATA_QUALITY_KEYS = ["lactate_stale", "lactate_never", "trends_not_ready"]


def text(key: str, lang: str, values: Optional[Dict[str, str]] = None) -> str:
    """Return one message in a language, with its {placeholders} filled in.

    If a Tamil or Hindi sentence is not written yet, the English one is used,
    so the app never shows an empty line.
    """
    template = MESSAGES[lang].get(key) or MESSAGES["en"][key]
    return template.format(**(values or {}))


def title(words: str) -> str:
    """Add a ":" after a section title, unless it already ends with "?" (as the Tamil one does)."""
    if words.endswith("?"):
        return words
    return words + ":"


def render_alert(bed: int, risk_pct: float, reason_items: List[Tuple[str, Dict[str, str]]], lang: str) -> str:
    """Build the full alert text: headline, reasons, data-quality notes, safety line.

    reason_items: list of (key, values), e.g. [("map_fell", {"value": "14"}), ("lactate_never", {})]
    """
    lines = [text("alert_headline", lang, {"bed": str(bed), "risk": f"{risk_pct:.1f}"})]
    reasons = [(key, values) for key, values in reason_items if key in REASON_KEYS]
    notes = [(key, values) for key, values in reason_items if key in DATA_QUALITY_KEYS]

    lines.append(title(text("why_now_title", lang)))
    if reasons:
        for key, values in reasons:
            lines.append("  • " + text(key, lang, values))
    else:
        lines.append("  • " + text("no_reason", lang))

    if notes:
        lines.append(title(text("data_quality_title", lang)))
        for key, values in notes:
            lines.append("  • " + text(key, lang, values))

    lines.append(text("safety_line", lang))
    return "\n".join(lines)
