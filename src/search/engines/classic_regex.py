from __future__ import annotations

import re

import pandas as pd

from ..normalize import normalize_text


def search_classic(df: pd.DataFrame, terms: list[str], top_k: int = 100) -> pd.DataFrame:
    if df.empty or not terms:
        return pd.DataFrame()

    df_local = df.copy()
    df_local["texto"] = df_local["texto"].astype(str)
    df_local["texto_normalizado"] = df_local["texto"].map(normalize_text)

    pattern = "|".join([rf"\b{re.escape(t)}\b" for t in terms])
    matches = df_local[df_local["texto_normalizado"].str.contains(pattern, na=False, regex=True)].copy()
    if matches.empty:
        return matches

    matches["matched_terms"] = matches["texto_normalizado"].apply(
        lambda txt: [term for term in terms if re.search(rf"\b{re.escape(term)}\b", txt)]
    )
    matches["score_total"] = matches["matched_terms"].str.len().astype(float)
    matches["fuente_score"] = "lexico"
    matches["razon_match"] = matches["matched_terms"].apply(lambda items: f"Coincidencia exacta: {', '.join(items)}")
    return matches.sort_values("score_total", ascending=False).head(top_k)
