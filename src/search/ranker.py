from __future__ import annotations

import pandas as pd


def apply_business_ranking(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "Fecha presentación" in out.columns:
        fechas = pd.to_datetime(out["Fecha presentación"], errors="coerce")
        recent_boost = fechas.rank(pct=True).fillna(0) * 0.05
        out["score_total"] = out["score_total"].astype(float) + recent_boost
    return out.sort_values("score_total", ascending=False)
