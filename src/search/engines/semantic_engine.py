from __future__ import annotations

from difflib import SequenceMatcher

import pandas as pd

from ..normalize import normalize_text


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def search_semantic(df: pd.DataFrame, query_text: str, top_k: int = 100, threshold: float = 0.18) -> pd.DataFrame:
    if df.empty or not query_text.strip():
        return pd.DataFrame()

    df_local = df.copy()
    q_norm = normalize_text(query_text)
    df_local["texto"] = df_local["texto"].astype(str)
    df_local["texto_normalizado"] = df_local["texto"].map(normalize_text)

    scores = []
    for text in df_local["texto_normalizado"]:
        target = text[:1200]
        scores.append(_similarity(q_norm, target))

    df_local["score_total"] = scores
    df_local = df_local[df_local["score_total"] >= threshold].copy()
    if df_local.empty:
        return df_local

    df_local["matched_terms"] = [[] for _ in range(len(df_local))]
    df_local["fuente_score"] = "semantico"
    df_local["razon_match"] = "Similitud semántica aproximada"
    return df_local.sort_values("score_total", ascending=False).head(top_k)
