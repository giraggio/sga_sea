from __future__ import annotations

from difflib import SequenceMatcher

import pandas as pd

from ..normalize import normalize_text, tokenize


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _token_overlap_score(query_tokens: set[str], doc_tokens: set[str]) -> float:
    if not query_tokens or not doc_tokens:
        return 0.0
    inter = len(query_tokens.intersection(doc_tokens))
    return inter / len(query_tokens)


def search_semantic(df: pd.DataFrame, query_text: str, top_k: int = 100, threshold: float = 0.08) -> pd.DataFrame:
    if df.empty or not query_text.strip():
        return pd.DataFrame()

    df_local = df.copy()
    q_norm = normalize_text(query_text)
    q_tokens = set(tokenize(q_norm))

    df_local["texto"] = df_local["texto"].astype(str)
    df_local["texto_normalizado"] = df_local["texto"].map(normalize_text)

    scores = []
    for text in df_local["texto_normalizado"]:
        target = text[:1800]
        seq = _similarity(q_norm, target)
        overlap = _token_overlap_score(q_tokens, set(tokenize(target)))
        score = (0.45 * seq) + (0.55 * overlap)
        scores.append(score)

    df_local["score_total"] = scores
    df_local = df_local[df_local["score_total"] >= threshold].copy()
    if df_local.empty:
        return df_local

    df_local["matched_terms"] = [[] for _ in range(len(df_local))]
    df_local["fuente_score"] = "semantico"
    df_local["razon_match"] = "Similitud semántica aproximada (overlap + secuencia)"
    return df_local.sort_values("score_total", ascending=False).head(top_k)
