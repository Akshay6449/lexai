# AI Agents

LexAI uses a **6-agent LangGraph pipeline** to analyze contracts. Each agent is a specialized module; `pipeline.py` orchestrates them as a stateful graph.

## Pipeline Overview

```
extract → classify → rag_retrieve → risk_analyze → recommend → approval_workflow
```

Defined in `backend/agents/pipeline.py`. Each node reads from and writes to `PipelineState` (a TypedDict).

## Agent 1: Document Extraction

**File:** `document_extraction_agent.py`

| | |
|---|---|
| **Input** | File path (PDF or DOCX) |
| **Output** | Raw text, document chunks, page count |
| **Libraries** | PyMuPDF (`fitz`), python-docx |

**What it does:**

1. Detects file type from extension
2. Extracts full text from the document
3. Cleans text (removes null bytes, normalizes whitespace)
4. Splits into chunks (~1500 chars) with section detection (e.g. "Section 8.2")
5. Returns `DocumentChunk` objects with index, text, char offsets, section ref

**Fallback:** If PyMuPDF is unavailable, returns stub text so the pipeline can still run in dev.

## Agent 2: Clause Classification

**File:** `clause_classification_agent.py`

| | |
|---|---|
| **Input** | Document chunks, contract type |
| **Output** | List of `ClassifiedClause` objects |
| **LLM** | Groq — `llama-3.1-70b-versatile` |

**Clause types (8):**

`confidentiality` | `liability` | `indemnification` | `termination` | `payment` | `data_privacy` | `intellectual_property` | `governing_law`

**What it does:**

1. Sends chunks to Groq with a structured JSON prompt
2. Parses returned clause list with type, text, section ref, confidence
3. Deduplicates overlapping clauses
4. Returns token usage for audit logging

## Agent 3: RAG Retrieval

**File:** `rag_retrieval_agent.py`

| | |
|---|---|
| **Input** | Classified clauses |
| **Output** | `ClauseWithRAG` — each clause + best playbook match |
| **Vector DB** | Qdrant (`lexai_playbooks` collection) |
| **Embeddings** | sentence-transformers/all-MiniLM-L6-v2 |

**What it does:**

1. Embeds each clause text
2. Performs ANN search in Qdrant (top-5, filtered by clause type)
3. Returns best match with similarity score, playbook title, standard text
4. Falls back to stub matches if Qdrant is unreachable

See [RAG and Qdrant](rag-and-qdrant.md) for vector setup.

## Agent 4: Risk Analysis

**File:** `risk_analysis_agent.py`

| | |
|---|---|
| **Input** | Clauses with RAG matches, contract type |
| **Output** | Per-clause risk + weighted contract risk score |
| **LLM** | Groq |

**Risk levels:**

| Score | Level |
|-------|-------|
| 0–24 | low |
| 25–49 | medium |
| 50–74 | high |
| 75–100 | critical |

**What it does:**

1. For each clause, compares original text against RAG standard text via Groq
2. Assigns per-clause risk score (0–100), level, explanation, business impact
3. Computes weighted contract score (indemnification and liability weighted higher)
4. Returns `ClauseRiskResult` list and aggregate contract score

## Agent 5: Recommendations

**File:** `recommendation_agent.py`

| | |
|---|---|
| **Input** | High/medium risk clauses with RAG context |
| **Output** | Suggested clause rewrites |
| **LLM** | Groq |

**What it does:**

1. For clauses above a risk threshold, generates alternative clause text
2. Explains business impact of accepting vs. negotiating
3. Returns `Recommendation` objects with original, suggested, and rationale

## Agent 6: Approval Workflow

**File:** `approval_workflow_agent.py`

| | |
|---|---|
| **Input** | Contract name, type, counterparty, risk score/level, recommendations |
| **Output** | Executive summary, approval routing decision |
| **LLM** | Groq |
| **Threshold** | `RISK_APPROVAL_THRESHOLD` (default 80) |

**What it does:**

1. Generates executive summary for legal leadership
2. Determines if contract requires manager approval (score >= threshold)
3. Provides routing reason
4. Pipeline creates an `Approval` DB record if approval is required

## LangGraph State

`PipelineState` fields:

| Field | Set by | Description |
|-------|--------|-------------|
| `contract_id`, `file_path`, `contract_type` | Input | Contract identifiers |
| `raw_text`, `chunks`, `page_count` | Agent 1 | Extraction output |
| `classified_clauses` | Agent 2 | Classified clause list |
| `clauses_with_rag` | Agent 3 | Clauses + playbook matches |
| `clause_risk_results`, `contract_risk_score`, `contract_risk_level` | Agent 4 | Risk output |
| `recommendations` | Agent 5 | Rewrite suggestions |
| `requires_approval`, `executive_summary`, `routing_reason` | Agent 6 | Workflow output |
| `total_tokens`, `errors` | All | Cumulative metadata |

## LangSmith Tracing

When `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY` is set, each agent's `run` method is traced via `@traceable` decorators. Traces appear in the LangSmith dashboard under project `LANGSMITH_PROJECT`.

## Error Handling

- Each pipeline node catches exceptions and appends to `state["errors"]`
- A failed agent does not crash the entire server — the contract may end in `error` status
- Partial results are persisted when possible

## Related Docs

- [Architecture](architecture.md) — pipeline diagram and data flow
- [RAG and Qdrant](rag-and-qdrant.md) — vector search detail
- [Configuration](configuration.md) — Groq and LangSmith settings
