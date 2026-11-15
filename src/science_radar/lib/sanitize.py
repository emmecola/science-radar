import re


# Patterns that turn third-party text into executable HTML/JS when the
# markdown artifacts are rendered by a publishing pipeline.
_UNSAFE_HTML_PATTERN = re.compile(
    r"<\s*(script|iframe|object|embed|svg|img|video|audio|link|meta|style)\b[^>]*>",
    re.IGNORECASE,
)
_UNSAFE_ATTR_PATTERN = re.compile(
    r"\bon[a-z]+\s*=", re.IGNORECASE
)
_JS_URL_PATTERN = re.compile(r"\((?:javascript|data|vbscript)\s*:", re.IGNORECASE)
_INJECTION_MARKERS = re.compile(
    r"(ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions"
    r"|system\s*(?:prompt|directive|message|note)"
    r"|disregard\s+(?:all\s+)?(?:previous|prior|above)"
    r"|you\s+are\s+now\s+operating"
    r"|<\|?(?:im_start|im_end|system|endoftext)\|?>)",
    re.IGNORECASE,
)
_INVISIBLE_CHARS = re.compile(
    "[\u200b\u200c\u200d\u200e\u200f\u202a-\u202e\u2060\u2061-\u2064\u2066-\u206f\ufeff\x00]"
)


def sanitize_untrusted(text: str) -> str:
    """Neutralize active HTML/JS and instruction-like markers in third-party text.

    Applied to fetched news/paper/snippet text before it is embedded into
    LLM prompts or written into published markdown artifacts.
    """
    if not isinstance(text, str):
        return text
    sanitized = _INVISIBLE_CHARS.sub("", text)
    sanitized = _UNSAFE_ATTR_PATTERN.sub("on_", sanitized)
    sanitized = _UNSAFE_HTML_PATTERN.sub("<blocked>", sanitized)
    sanitized = _JS_URL_PATTERN.sub("(blocked:", sanitized)
    sanitized = _INJECTION_MARKERS.sub("[untrusted-content-marker]", sanitized)
    return sanitized


def sanitize_untrusted_json(payload: str) -> str:
    """Sanitize a JSON string of third-party items field-by-field."""
    import json

    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, TypeError):
        return sanitize_untrusted(payload)
    if not isinstance(data, list):
        return sanitize_untrusted(payload)
    cleaned = [
        {key: sanitize_untrusted(value) if isinstance(value, str) else value for key, value in item.items()}
        if isinstance(item, dict)
        else item
        for item in data
    ]
    return json.dumps(cleaned, indent=2)