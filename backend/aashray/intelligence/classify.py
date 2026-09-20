from __future__ import annotations

from aashray.services.llm import classify_text as llm_classify

_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("landslide", ("landslide", "debris", "slope", "hillside")),
    ("blocked_road", ("blocked", "road blocked", "debris on road")),
    ("trapped", ("trapped", "vehicle trapped", "stuck")),
]


def classify(raw_text: str | None) -> dict:
    """LLM if configured; keyword fallback. Never returns coordinates."""
    if not raw_text:
        return {}
    parsed = llm_classify(raw_text)
    if isinstance(parsed, dict) and parsed.get("emergency_type"):
        return {
            "emergency_type": parsed.get("emergency_type"),
            "severity": parsed.get("severity"),
            "people_count": parsed.get("people_count"),
            "source": "llm",
        }
    low = raw_text.lower()
    for label, words in _KEYWORDS:
        if any(w in low for w in words):
            return {"emergency_type": label, "source": "keyword"}
    return {}
