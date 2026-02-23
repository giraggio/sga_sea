from __future__ import annotations

import re

from .normalize import normalize_text, tokenize


_QUOTED_RE = re.compile(r'"([^"]+)"')
_STOPWORDS = {
    "de", "del", "la", "las", "el", "los", "y", "o", "u", "en", "por", "para", "con",
    "a", "al", "que", "se", "un", "una", "sobre", "si", "existe", "algun", "alguna"
}


def split_terms(query: str, strict: bool = False) -> list[str]:
    """
    - strict=True: solo frases entre comillas y términos separados por coma (modo clásico).
    - strict=False: además agrega tokens útiles de lenguaje natural para modos no clásicos.
    """
    quoted = [normalize_text(match) for match in _QUOTED_RE.findall(query)]
    remainder = _QUOTED_RE.sub("", query)
    comma_terms = [normalize_text(item) for item in remainder.split(",") if item.strip()]

    base_terms = [term for term in quoted + comma_terms if term]
    if strict:
        return base_terms

    token_terms: list[str] = []
    for term in base_terms:
        toks = [t for t in tokenize(term) if t not in _STOPWORDS and len(t) > 2]
        token_terms.extend(toks)

    if not base_terms:
        token_terms.extend([t for t in tokenize(query) if t not in _STOPWORDS and len(t) > 2])

    merged = base_terms + token_terms
    seen = set()
    out: list[str] = []
    for t in merged:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


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
