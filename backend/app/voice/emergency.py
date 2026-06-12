"""
CareVoice AI Hospital Platform - Emergency Detection.

Deterministic keyword checking to quickly flag emergency/critical care indicators
and escalate call processing.
"""

import re

# Set of common medical emergency terms/phrases
EMERGENCY_KEYWORDS = {
    r"\bchest\s+pain\b",
    r"\bheart\s+attack\b",
    r"\bbreathless(ness)?\b",
    r"\bdifficulty\s+breathing\b",
    r"\bstroke\b",
    r"\bseizure\b",
    r"\bunconscious(ness)?\b",
    r"\bheavy\s+bleeding\b",
    r"\bsevere\s+burn\b",
    r"\bsuicid(al|e)\b",
    r"\bchoking\b",
    r"\bpoison(ed|ing)?\b",
    r"\bparaly(sis|zed)\b",
    r"\bhead\s+trauma\b",
    r"\bbroken\s+neck\b",
}


def is_emergency(text: str) -> bool:
    """Deterministically analyze patient-reported symptoms for life-threatening keywords.

    Args:
        text: Patient symptom transcript

    Returns:
        bool: True if emergency keywords are flagged, otherwise False.
    """
    if not text:
        return False
    
    normalized_text = text.lower().strip()
    
    for pattern in EMERGENCY_KEYWORDS:
        if re.search(pattern, normalized_text):
            return True
            
    return False
