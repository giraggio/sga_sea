# Cómo implementar esta arquitectura en tu repositorio

## 1) Copiar estructura mínima
Crea estos directorios/archivos:

```bash
mkdir -p src/search/engines src/indexing
```

Archivos clave:
- `src/search/service.py`
- `src/search/query_parser.py`
- `src/search/normalize.py`
- `src/search/engines/classic_regex.py`
- `src/search/engines/bm25_engine.py`
- `src/search/engines/semantic_engine.py`
- `src/search/engines/hybrid_engine.py`
- `src/search/ranker.py`

## 2) Integrar en la UI
En tu Streamlit/app:
1. Importa `from src.search import search`.
2. Agrega selector de modo: `clasico`, `lexico`, `semantico`, `hibrido`.
3. Reemplaza el filtro regex directo por llamada a:

```python
resultados = search(query=consulta, fuente=fuente, modo=modo, filtros={}, top_k=200, dataset=df)
```

## 3) Mantener compatibilidad
- Deja `modo=clasico` como default.
- Conserva filtros existentes (región/estado/fecha) después de la búsqueda.

## 4) Validar localmente
Ejecuta:

```bash
python -m compileall buscador_palabras.py src
python - <<'PY'
import pandas as pd
from src.search import search

df = pd.DataFrame([
    {"texto":"Nothofagus dombeyi en área prioritaria", "url":"u1", "proyecto_origen":"p1"},
    {"texto":"afectación de suelos por derrame", "url":"u2", "proyecto_origen":"p2"},
])
print(search('"Nothofagus dombeyi"', 'CAV', 'clasico', {}, 5, df)[['url','score_total']])
print(search('plan de afectación de suelos por derrame', 'CAV', 'hibrido', {}, 5, df)[['url','score_total']])
PY
```

## 5) Despliegue incremental recomendado
1. Publicar primero `clasico` + `lexico`.
2. Activar `semantico` detrás de feature flag.
3. Medir métricas de no-regresión antes de dejar `hibrido` como recomendado.

## Nota
Si no te sirve la expansión por sinónimos, déjala fuera (como en esta implementación), y prioriza exact match + ranking híbrido.


## 6) Si fuera del modo clásico salen pocos o cero resultados
Ajusta estos parámetros primero:
- En `src/search/query_parser.py`: usar `split_terms(..., strict=False)` para extraer tokens útiles desde consultas largas.
- En `src/search/engines/semantic_engine.py`: bajar `threshold` (ej. `0.12 -> 0.08`).
- En híbrido: verificar que `search_lexical(...)` reciba términos tokenizados y no solo frases completas.

Checklist rápido:
1. ¿La consulta trae comas/comillas? (si no, tokeniza automáticamente para modo no clásico).
2. ¿Los términos tienen stopwords predominantes? (filtrarlas mejora recall).
3. ¿El umbral semántico está demasiado alto para tu corpus?
