from __future__ import annotations

import re

from .normalize import normalize_text


_QUOTED_RE = re.compile(r'"([^"]+)"')


def split_terms(query: str) -> list[str]:
    quoted = [normalize_text(match) for match in _QUOTED_RE.findall(query)]
    remainder = _QUOTED_RE.sub("", query)
    comma_terms = [normalize_text(item) for item in remainder.split(",") if item.strip()]
    return [term for term in quoted + comma_terms if term]


def infer_intent(query: str) -> str:
    q = query.strip()
    q_norm = normalize_text(q)
    tokens = q_norm.split()

    if len(tokens) <= 3 and any(ch in q for ch in ['"', "'"]):
        return "estricta"

    latin_binomial = re.search(r"\b[a-z]+\s+[a-z]{3,}\b", q_norm)
    if len(tokens) <= 4 and latin_binomial:
        return "estricta"

    if len(tokens) >= 8 or any(word in q_norm for word in ["necesito", "existe", "adenda", "observacion"]):
        return "amplia"

    return "semiestricta"
