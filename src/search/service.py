from __future__ import annotations

from typing import Dict

import pandas as pd

from .engines.bm25_engine import search_lexical
from .engines.classic_regex import search_classic
from .engines.hybrid_engine import merge_hybrid
from .engines.semantic_engine import search_semantic
from .query_parser import infer_intent, split_terms
from .ranker import apply_business_ranking


def _ensure_doc_id(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "doc_id" not in out.columns:
        out["doc_id"] = out.index.astype(str)
    return out


def search(
    query: str,
    fuente: str,
    modo: str,
    filtros: Dict[str, object] | None,
    top_k: int,
    dataset: pd.DataFrame,
) -> pd.DataFrame:
    filtros = filtros or {}
    df = _ensure_doc_id(dataset)
    intent = infer_intent(query)

    terms = split_terms(query)
    expanded_terms = terms

    if modo == "clasico":
        result = search_classic(df, expanded_terms, top_k=top_k)
    elif modo == "lexico":
        result = search_lexical(df, expanded_terms, top_k=top_k)
    elif modo == "semantico":
        result = search_semantic(df, query, top_k=top_k)
    else:
        lexical = search_lexical(df, expanded_terms, top_k=max(top_k, 200))
        semantic = search_semantic(df, query, top_k=max(top_k, 200))
        result = merge_hybrid(lexical, semantic, top_k=top_k)
        if not result.empty:
            cols = [c for c in df.columns if c not in result.columns]
            result = result.merge(df[["doc_id", *cols]], on="doc_id", how="left")

    if result.empty:
        return result

    result["intent_detectada"] = intent
    result = apply_business_ranking(result)
    return result.head(top_k)
