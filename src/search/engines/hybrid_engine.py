from __future__ import annotations

import pandas as pd


def merge_hybrid(lexical_df: pd.DataFrame, semantic_df: pd.DataFrame, top_k: int = 100) -> pd.DataFrame:
    if lexical_df.empty and semantic_df.empty:
        return pd.DataFrame()
    if lexical_df.empty:
        out = semantic_df.copy()
        out["fuente_score"] = "semantico"
        return out.head(top_k)
    if semantic_df.empty:
        out = lexical_df.copy()
        out["fuente_score"] = "lexico"
        return out.head(top_k)

    left = lexical_df[["doc_id", "score_total", "matched_terms", "razon_match"]].rename(
        columns={"score_total": "score_lexico", "razon_match": "razon_lexico"}
    )
    right = semantic_df[["doc_id", "score_total", "razon_match"]].rename(
        columns={"score_total": "score_semantico", "razon_match": "razon_semantico"}
    )

    merged = left.merge(right, on="doc_id", how="outer")
    merged["score_lexico"] = merged["score_lexico"].fillna(0.0)
    merged["score_semantico"] = merged["score_semantico"].fillna(0.0)

    max_lex = max(float(merged["score_lexico"].max()), 1e-9)
    max_sem = max(float(merged["score_semantico"].max()), 1e-9)
    merged["score_total"] = 0.65 * (merged["score_lexico"] / max_lex) + 0.35 * (merged["score_semantico"] / max_sem)

    merged["fuente_score"] = "hibrido"
    merged["razon_match"] = merged.apply(
        lambda r: f"Híbrido (lex={r['score_lexico']:.3f}, sem={r['score_semantico']:.3f})", axis=1
    )
    return merged.sort_values("score_total", ascending=False).head(top_k)
