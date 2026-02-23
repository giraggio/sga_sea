from __future__ import annotations

import re
import unicodedata


_SPACE_RE = re.compile(r"\s+")
_NON_WORD_RE = re.compile(r"[^\w\s]")


def strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")


def normalize_text(text: str) -> str:
    text = str(text or "").lower()
    text = strip_accents(text)
    text = _NON_WORD_RE.sub(" ", text)
    text = _SPACE_RE.sub(" ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [token for token in normalized.split(" ") if token]
