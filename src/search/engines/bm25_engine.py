from __future__ import annotations

import math
from collections import Counter

import pandas as pd

from ..normalize import tokenize


def search_lexical(df: pd.DataFrame, terms: list[str], top_k: int = 100) -> pd.DataFrame:
    if df.empty or not terms:
        return pd.DataFrame()

    df_local = df.copy()
    df_local["texto"] = df_local["texto"].astype(str)
    token_docs = df_local["texto"].apply(tokenize)
    df_local["_tokens"] = token_docs

    doc_freq: Counter[str] = Counter()
    for toks in token_docs:
        doc_freq.update(set(toks))

    n_docs = len(df_local)
    avgdl = max(sum(len(toks) for toks in token_docs) / max(n_docs, 1), 1)
    k1 = 1.5
    b = 0.75

    scores = []
    matched_terms = []
    for toks in token_docs:
        tf = Counter(toks)
        dl = len(toks)
        score = 0.0
        matched = []
        for term in terms:
            if term not in tf:
                continue
            matched.append(term)
            df_term = doc_freq.get(term, 0)
            idf = math.log(1 + (n_docs - df_term + 0.5) / (df_term + 0.5))
            numerador = tf[term] * (k1 + 1)
            denominador = tf[term] + k1 * (1 - b + b * dl / avgdl)
            score += idf * (numerador / denominador)
        scores.append(score)
        matched_terms.append(matched)

    df_local["matched_terms"] = matched_terms
    df_local["score_total"] = scores
    df_local = df_local[df_local["score_total"] > 0].copy()
    if df_local.empty:
        return df_local
    df_local["fuente_score"] = "lexico"
    df_local["razon_match"] = df_local["matched_terms"].apply(lambda items: f"BM25: {', '.join(items)}")
    return df_local.sort_values("score_total", ascending=False).head(top_k)
