from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class SearchQuery:
    query: str
    fuente: str
    modo: str = "clasico"
    filtros: Dict[str, object] = field(default_factory=dict)
    top_k: int = 100


@dataclass
class SearchResult:
    doc_id: str
    texto: str
    url: Optional[str]
    proyecto_origen: Optional[str]
    score_total: float
    fuente_score: str
    razon_match: str
    metadata: Dict[str, object] = field(default_factory=dict)
    matched_terms: List[str] = field(default_factory=list)
