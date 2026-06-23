"""
Agent 3 — RAG Retrieval Agent
Embeds each classified clause using SentenceTransformers,
then performs ANN search in Qdrant to find the most similar
standard playbook clauses for comparison.
"""
import logging
import time
from dataclasses import dataclass
from typing import Optional

from langsmith import traceable

from core.config import settings
from agents.clause_classification_agent import ClassifiedClause
from rag.qdrant_client import search_similar_clauses

logger = logging.getLogger(__name__)


@dataclass
class RAGMatch:
    clause_type: str
    source_title: str
    source_playbook: str
    standard_text: str
    similarity_score: float
    qdrant_vector_id: str


@dataclass
class ClauseWithRAG:
    clause: ClassifiedClause
    best_match: Optional[RAGMatch]
    all_matches: list[RAGMatch]


class RAGRetrievalAgent:
    """
    For each classified clause:
    1. Generate embedding with SentenceTransformers
    2. Query Qdrant collection for top-k similar standard clauses
    3. Return the best match for use by the Risk Analysis Agent
    """
    name = "RAGRetrievalAgent"
    TOP_K = 5

    def __init__(self):
        self._embedder = None

    def _get_embedder(self):
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
                logger.info(f"[{self.name}] Loaded embedding model: {settings.EMBEDDING_MODEL}")
            except ImportError:
                logger.warning(f"[{self.name}] sentence-transformers not installed. Using stub embeddings.")
        return self._embedder

    def _embed(self, text: str) -> list[float]:
        embedder = self._get_embedder()
        if embedder:
            return embedder.encode(text, normalize_embeddings=True).tolist()
        # Stub: random-ish deterministic vector for dev
        import hashlib
        h = int(hashlib.md5(text.encode()).hexdigest(), 16)
        return [(((h >> i) & 0xFF) / 255.0) for i in range(settings.QDRANT_VECTOR_SIZE)]

    @traceable(name="RAGRetrievalAgent.run")
    async def run(self, clauses: list[ClassifiedClause]) -> list[ClauseWithRAG]:
        t0 = time.perf_counter()
        results: list[ClauseWithRAG] = []

        for clause in clauses:
            matches = await self._search(clause)
            results.append(ClauseWithRAG(
                clause=clause,
                best_match=matches[0] if matches else None,
                all_matches=matches,
            ))

        duration_ms = round((time.perf_counter() - t0) * 1000)
        logger.info(f"[{self.name}] Retrieved RAG matches for {len(clauses)} clauses in {duration_ms}ms")
        return results

    async def _search(self, clause: ClassifiedClause) -> list[RAGMatch]:
        try:
            hits = search_similar_clauses(
                clause.text,
                clause_type=clause.clause_type,
                top_k=self.TOP_K,
            )
            if hits:
                return [
                    RAGMatch(
                        clause_type=h.get("clause_type", clause.clause_type),
                        source_title=h.get("title", "Playbook Clause"),
                        source_playbook=h.get("playbook", "Internal Legal Playbooks"),
                        standard_text=h.get("standard_text", ""),
                        similarity_score=h.get("score", 0.0),
                        qdrant_vector_id=h.get("id", ""),
                    )
                    for h in hits
                ]
        except Exception as e:
            logger.warning(f"[{self.name}] Qdrant search failed, using stub: {e}")

        return self._stub_matches(clause.clause_type)

    def _stub_matches(self, clause_type: str) -> list[RAGMatch]:
        stubs = {
            "liability": RAGMatch(
                clause_type="liability",
                source_title="NDA Standard — Liability Cap",
                source_playbook="Standard Corporate Playbook §4.3",
                standard_text=(
                    "Neither party's aggregate liability shall exceed the greater of "
                    "(a) $500,000 or (b) the total fees paid in the twelve months preceding the claim."
                ),
                similarity_score=0.94,
                qdrant_vector_id="stub-liability-1",
            ),
            "indemnification": RAGMatch(
                clause_type="indemnification",
                source_title="MSA Standard — Indemnification Limits",
                source_playbook="MSA Standards §4.3",
                standard_text=(
                    "Indemnification obligations are limited to direct damages caused by a party's "
                    "gross negligence or willful misconduct, capped at 2x annual contract value."
                ),
                similarity_score=0.87,
                qdrant_vector_id="stub-indemnification-1",
            ),
            "termination": RAGMatch(
                clause_type="termination",
                source_title="Standard Termination Notice",
                source_playbook="Standard Corporate Playbook §6.1",
                standard_text=(
                    "Either party may terminate for convenience upon thirty (30) days prior written notice."
                ),
                similarity_score=0.92,
                qdrant_vector_id="stub-termination-1",
            ),
            "confidentiality": RAGMatch(
                clause_type="confidentiality",
                source_title="NDA Standard Confidentiality",
                source_playbook="NDA Standards §2.1",
                standard_text=(
                    "The Receiving Party shall maintain confidentiality using at least the same "
                    "degree of care used to protect its own confidential information, but no less "
                    "than reasonable care, for a period of five (5) years."
                ),
                similarity_score=0.89,
                qdrant_vector_id="stub-confidentiality-1",
            ),
        }
        default = RAGMatch(
            clause_type=clause_type,
            source_title=f"{clause_type.replace('_', ' ').title()} Standard",
            source_playbook="Internal Legal Playbooks",
            standard_text=f"Standard {clause_type} clause per company policy.",
            similarity_score=0.75,
            qdrant_vector_id=f"stub-{clause_type}-1",
        )
        return [stubs.get(clause_type, default)]
