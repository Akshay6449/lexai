"""
Agent 2 — Clause Classification Agent
Uses Groq LLaMA 3.1 70B to identify and classify legal clause types across 8 categories.
Returns structured clause objects with section references and confidence scores.
"""
import json
import logging
import time
from dataclasses import dataclass
from typing import Optional

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable

from core.config import settings
from agents.document_extraction_agent import DocumentChunk

logger = logging.getLogger(__name__)

CLAUSE_TYPES = [
    "confidentiality",
    "liability",
    "indemnification",
    "termination",
    "payment",
    "data_privacy",
    "intellectual_property",
    "governing_law",
]


@dataclass
class ClassifiedClause:
    clause_type: str
    text: str
    section_ref: Optional[str]
    confidence: float
    chunk_index: int


CLASSIFICATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior legal analyst specializing in contract review.
Analyze the provided contract text chunks and identify legal clauses.

For EACH distinct clause found, return a JSON object in this exact format:
{{
  "clauses": [
    {{
      "clause_type": "<one of: confidentiality|liability|indemnification|termination|payment|data_privacy|intellectual_property|governing_law>",
      "text": "<exact verbatim text of the clause>",
      "section_ref": "<section number if visible, e.g. Section 8.2, else null>",
      "confidence": <float 0.0-1.0>,
      "chunk_index": <integer>
    }}
  ]
}}

Rules:
- Only output valid JSON, no preamble or explanation.
- A single chunk may contain multiple clauses — extract them all.
- If a chunk has no recognizable legal clause, include nothing for it.
- confidence reflects how certain you are of the classification (0.95+ = very confident).
- Use "text" to capture the FULL clause text, not just the heading.
"""),
    ("human", """Contract type: {contract_type}

Analyze these text chunks and extract all legal clauses:

{chunks_text}

Return only the JSON object."""),
])


class ClauseClassificationAgent:
    name = "ClauseClassificationAgent"

    def __init__(self):
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=settings.GROQ_TEMPERATURE,
            max_tokens=settings.GROQ_MAX_TOKENS,
            api_key=settings.GROQ_API_KEY,
        )
        self.chain = CLASSIFICATION_PROMPT | self.llm

    @traceable(name="ClauseClassificationAgent.run")
    async def run(
        self,
        chunks: list[DocumentChunk],
        contract_type: str,
    ) -> tuple[list[ClassifiedClause], int, Optional[str]]:
        """
        Returns (classified_clauses, total_tokens_used, error_message).
        error_message is set when the LLM call or JSON parse fails.
        """
        t0 = time.perf_counter()
        all_clauses: list[ClassifiedClause] = []
        total_tokens = 0
        last_error: Optional[str] = None

        BATCH_SIZE = 5
        for batch_start in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[batch_start: batch_start + BATCH_SIZE]
            clauses, tokens, batch_error = await self._classify_batch(batch, contract_type)
            all_clauses.extend(clauses)
            total_tokens += tokens
            if batch_error:
                last_error = batch_error

        deduped = self._deduplicate(all_clauses)

        duration_ms = round((time.perf_counter() - t0) * 1000)
        logger.info(
            f"[{self.name}] Classified {len(deduped)} clauses "
            f"from {len(chunks)} chunks in {duration_ms}ms ({total_tokens} tokens)"
        )
        if chunks and not deduped and not last_error:
            last_error = (
                f"no clauses extracted from {len(chunks)} chunks "
                f"(model={settings.GROQ_MODEL})"
            )
            logger.warning(f"[{self.name}] {last_error}")
        return deduped, total_tokens, last_error

    async def _classify_batch(
        self,
        chunks: list[DocumentChunk],
        contract_type: str,
    ) -> tuple[list[ClassifiedClause], int, Optional[str]]:
        chunks_text = "\n\n---CHUNK BOUNDARY---\n\n".join(
            f"[Chunk {c.index}]{' ' + c.section_ref if c.section_ref else ''}\n{c.text}"
            for c in chunks
        )

        raw = ""
        try:
            response = await self.chain.ainvoke({
                "contract_type": contract_type,
                "chunks_text": chunks_text,
            })
            raw = response.content.strip()
            tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

            # Parse JSON, strip any markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)

            clauses = []
            for item in data.get("clauses", []):
                if item.get("clause_type") not in CLAUSE_TYPES:
                    continue
                clauses.append(ClassifiedClause(
                    clause_type=item["clause_type"],
                    text=item.get("text", ""),
                    section_ref=item.get("section_ref"),
                    confidence=float(item.get("confidence", 0.7)),
                    chunk_index=int(item.get("chunk_index", 0)),
                ))
            return clauses, tokens, None

        except (json.JSONDecodeError, KeyError) as e:
            preview = raw[:200]
            msg = f"JSON parse error: {e}"
            logger.error(f"[{self.name}] {msg} | model={settings.GROQ_MODEL} | response={preview!r}")
            return [], 0, msg
        except Exception as e:
            msg = f"LLM call failed: {e} (model={settings.GROQ_MODEL})"
            logger.error(f"[{self.name}] {msg}")
            return [], 0, msg

    def _deduplicate(self, clauses: list[ClassifiedClause]) -> list[ClassifiedClause]:
        """Keep all clauses but remove near-identical duplicates (same type + first 80 chars)."""
        seen: set[str] = set()
        result: list[ClassifiedClause] = []
        for c in sorted(clauses, key=lambda x: -x.confidence):
            key = f"{c.clause_type}:{c.text[:80].lower().strip()}"
            if key not in seen:
                seen.add(key)
                result.append(c)
        return result
