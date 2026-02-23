# Arquitectura propuesta de búsqueda (sin romper lo actual)

## Objetivo
Evolucionar el buscador actual de coincidencias por palabra clave hacia un sistema híbrido (léxico + semántico), manteniendo **compatibilidad total** con el flujo vigente de Streamlit y sus filtros.

## Principios de diseño
1. **Backward compatible**: el modo actual de regex sigue existiendo como `modo=clasico`.
2. **Desacoplar indexación de consulta**: construir índices offline y consultar online.
3. **Degradación segura**: si falla el motor semántico, responder con motor clásico/BM25.
4. **Explicabilidad**: cada resultado muestra por qué apareció (match léxico, match semántico, score final).

## Arquitectura en capas

### 1) Capa de datos (ya existente + normalización)
- Fuentes actuales JSONL comprimidas por tipo documental (`CAV`, `ICC`, `MEDIDAS`, `PPCE`, `EVI`, `ICT`).
- Tabla de metadatos de proyectos (`seia_filtrado.xlsx`).
- Nuevo paso de normalización de texto:
  - lowercase
  - remoción de tildes
  - limpieza de espacios/símbolos
  - opcional: lematización liviana para español

**Salida:** dataset canónico por documento con campos:
- `doc_id`
- `texto_original`
- `texto_normalizado`
- `url`
- `proyecto_origen`
- metadatos (`Región`, `Estado`, `Fecha presentación`, etc.)

### 2) Capa de indexación (offline)

#### 2.1 Índice léxico (BM25)
- Construir un índice BM25 sobre `texto_normalizado`.
- Persiste en disco (por ejemplo, `artifacts/indexes/bm25/<fuente>.pkl`).

#### 2.2 Índice vectorial (semántico)
- Modelo de embeddings en español (ej: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` como punto de partida).
- Generar embeddings por documento/chunk.
- Indexar en FAISS (`IndexFlatIP` o HNSW).
- Persiste en disco (`artifacts/indexes/faiss/<fuente>.index`) + mapping `doc_id`.

#### 2.3 Diccionario de sinónimos de dominio
- (Opcional) archivo de sinónimos de dominio, solo si negocio lo requiere.

### 3) Capa de consulta (online)

#### 3.1 API interna de búsqueda (módulo Python)
Crear un servicio interno/módulo con interfaz estable:

```python
search(query: str, fuente: str, modo: str, filtros: dict, top_k: int = 100) -> pd.DataFrame
```

Modos:
- `clasico`: regex actual (compatibilidad)
- `lexico`: BM25
- `semantico`: FAISS + embeddings
- `hibrido`: fusión BM25 + semántico (RRF o suma ponderada)

#### 3.2 Flujo de resolución de consulta
1. Parsear consulta (frases, operadores opcionales, expansión por sinónimos).
2. Recuperar candidatos por motor(es).
3. Fusionar/normalizar score.
4. Aplicar filtros de negocio (Región, Estado, Fecha).
5. Re-rank final (boost por recencia/estado crítico/opcional).
6. Entregar resultados + campos de explicabilidad.

### 4) Capa de presentación (Streamlit, sin romper UI)
Cambios mínimos en UI:
- Mantener input actual de palabras clave.
- Agregar selector “Modo de búsqueda”:
  - Clásico (actual)
  - Léxico avanzado
  - Semántico
  - Híbrido (recomendado)
- Mantener filtros existentes tal cual.
- Agregar columnas:
  - `score_total`
  - `fuente_score` (léxico/semántico/híbrido)
  - `razon_match`

## Estructura de código sugerida

```text
sga_sea/
  buscador_palabras.py                # UI Streamlit
  src/
    search/
      __init__.py
      models.py                       # dataclasses de Query/Result
      normalize.py                    # normalización de texto
      query_parser.py                 # parsing de consulta e intención
      engines/
        classic_regex.py              # lógica actual encapsulada
        bm25_engine.py
        semantic_engine.py
        hybrid_engine.py
      ranker.py                       # fusión y reranking
      service.py                      # función search(...)
    indexing/
      build_corpus.py
      build_bm25.py
      build_embeddings.py
      build_faiss.py
  artifacts/
    indexes/
      bm25/
      faiss/
```

## Plan de migración incremental

### Fase 0 (1-2 días)
- Encapsular la lógica regex actual en `classic_regex.py`.
- Mantener comportamiento idéntico al actual.

### Fase 1 (2-4 días)
- Implementar normalización de texto + BM25.
- Agregar `modo=lexico` en UI.
- Validar precisión con set de consultas reales.

### Fase 2 (3-5 días)
- Implementar embeddings + FAISS.
- Agregar `modo=semantico` y `modo=hibrido`.
- Incluir fallback automático a BM25 si falla FAISS/modelo.

### Fase 3 (2-3 días)
- Explicabilidad + ajustes de ranking por metadatos.
- Métricas y tablero de evaluación offline.

## Estrategia de calidad
- Tests unitarios de:
  - parser de consulta
  - normalización
  - fusión de scores
- Tests de regresión:
  - `modo=clasico` debe entregar resultados equivalentes al estado actual.
- Evaluación offline con set dorado:
  - Precision@10
  - Recall@50
  - NDCG@10

## Operación y performance
- Cachear índices en memoria con `st.cache_resource`.
- Cachear cargas de datasets con `st.cache_data`.
- Construcción de índices por tarea batch programada (diaria/semanal).
- Observabilidad mínima:
  - tiempo de respuesta por consulta
  - motor usado
  - número de resultados

## Riesgos y mitigaciones
- **Riesgo:** latencia por embeddings en runtime.
  - **Mitigación:** pre-indexar offline y solo embed de query online.
- **Riesgo:** resultados semánticos poco precisos en dominio ambiental.
  - **Mitigación:** enfoque híbrido + sinónimos de negocio + evaluación continua.
- **Riesgo:** complejidad de mantenimiento.
  - **Mitigación:** interfaz única `search(...)` y engines desacoplados.

## Definición de éxito
- Mantener 100% de compatibilidad del modo clásico.
- Reducir “búsquedas sin resultados” al menos 30%.
- Mejorar Precision@10 del top de resultados en consultas complejas.

## Cómo testear la propuesta antes de implementarla
Puedes validarla con bajo riesgo mediante una evaluación offline ("shadow mode") comparando todo contra el baseline actual.

### 1) Construir un set de consultas representativo
Crear un archivo versionado (ej. `docs/eval_queries.csv`) con:
- `query`
- `tipo_consulta` (`estricta`, `semiestricta`, `amplia`)
- `fuente_esperada` (`CAV`, `ICC`, `PPCE`, etc.)
- `doc_ids_relevantes` (ground truth)
- `fragmentos_referencia` (si existen)

Sugerencia inicial: 90 consultas (30 por tipo).

### 2) Medir baseline (modo actual)
Evaluar `modo=clasico` primero y guardar resultados base:
- Precision@10
- Recall@50
- NDCG@10
- % de consultas sin resultados
- Latencia p95

### 3) Ejecutar comparación en shadow mode
Sin tocar producción, correr un runner offline para cada consulta en:
- `clasico`
- `lexico`
- `semantico`
- `hibrido`

Guardar salida en `artifacts/eval_runs/<fecha>.parquet` con ranking, score, latencia y tipo de match.

### 4) Incluir pruebas específicas para documentos largos
Para expedientes con cientos de páginas, evaluar sensibilidad con matriz:
- chunk size: 600 / 800 / 1000
- overlap: 80 / 120 / 160
- top-k chunks: 100 / 200

Y monitorear:
- latencia p95 por consulta,
- cobertura de pasajes explicativos,
- estabilidad de ranking entre configuraciones.

### 5) Definir gates de no-regresión (go/no-go)
- Consultas `estricta`: **cero regresión** vs baseline.
- Consultas `semiestricta` y `amplia`: mejora en al menos 2 métricas (por ejemplo Recall@50 y NDCG@10).
- Umbral operacional: latencia p95 dentro del SLA definido por negocio.

### 6) UAT rápida con analistas (antes de implementación)
Hacer una comparación ciega A/B de resultados (sin mostrar motor) y capturar:
- preferencia de relevancia,
- utilidad de la evidencia (fragmento),
- confianza para decisión.

Con esto puedes validar si la arquitectura agrega valor real antes de modificar el flujo actual de Streamlit.
