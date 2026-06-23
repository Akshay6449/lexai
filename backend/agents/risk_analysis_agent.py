"""
Agent 4 — Risk Analysis Agent
Analyzes each clause against its RAG match and contract-level context.
Produces a risk score (0–100) and risk level (low/medium/high/critical)
for each clause, then computes the aggregate contract risk score.
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
from agents.rag_retrieval_agent import ClauseWithRAG

logger = logging.getLogger(__name__)


@dataclass
class ClauseRiskResult:
    clause_type: str
    original_text: str
    section_ref: Optional[str]
    confidence: float
    risk_score: int               # 0–100
    risk_level: str               # low|medium|high|critical
    explanation: str
    business_impact: str
    rag_source: Optional[str]
    rag_similarity: Optional[float]


@dataclass
class ContractRiskResult:
    clause_results: list[ClauseRiskResult]
    contract_risk_score: int      # weighted aggregate 0–100
    contract_risk_level: str
    tokens_used: int
    duration_ms: int


RISK_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a legal risk analyst at a Fortune 500 company.
Evaluate the provided contract clause for legal and business risk.

Compare it against the standard/playbook version and output ONLY this JSON:
{{
  "risk_score": <integer 0-100>,
  "risk_level": "<low|medium|high|critical>",
  "explanation": "<2-3 sentences explaining the risk>",
  "business_impact": "<1-2 sentences on financial/operational business impact>"
}}

Risk scoring guide:
- 0–25: Low — clause is standard or better than playbook
- 26–50: Medium — minor deviations, negotiate if possible
- 51–75: High — significant risk, requires legal review and amendment
- 76–100: Critical — do not execute without major renegotiation

Output ONLY valid JSON, no explanation outside the JSON block.
"""),
    ("human", """Contract type: {contract_type}
Clause type: {clause_type}
Section: {section_ref}

CURRENT CLAUSE:
{clause_text}

PLAYBOOK STANDARD (similarity: {similarity}):
{standard_text}

Analyze the risk and output JSON:"""),
])


class RiskAnalysisAgent:
    name = "RiskAnalysisAgent"

    # Clause-type weight multipliers for contract-level score
    WEIGHTS = {
        "indemnification": 1.5,
        "liability": 1.4,
        "data_privacy": 1.3,
        "intellectual_property": 1.2,
        "termination": 1.0,
        "confidentiality": 1.0,
        "payment": 0.8,
        "governing_law": 0.5,
    }

    def __init__(self):
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=0.05,       # low temperature for consistent scoring
            max_tokens=512,
            api_key=settings.GROQ_API_KEY,
        )
        self.chain = RISK_ANALYSIS_PROMPT | self.llm

    @traceable(name="RiskAnalysisAgent.run")
    async def run(
        self,
        clauses_with_rag: list[ClauseWithRAG],
        contract_type: str,
    ) -> ContractRiskResult:
        t0 = time.perf_counter()
        results: list[ClauseRiskResult] = []
        total_tokens = 0

        for cwr in clauses_with_rag:
            result, tokens = await self._analyze_clause(cwr, contract_type)
            results.append(result)
            total_tokens += tokens

        contract_score = self._compute_contract_score(results)
        contract_level = self._score_to_level(contract_score)

        duration_ms = round((time.perf_counter() - t0) * 1000)
        logger.info(
            f"[{self.name}] Contract risk: {contract_score} ({contract_level}) "
            f"| {len(results)} clauses | {total_tokens} tokens | {duration_ms}ms"
        )

        return ContractRiskResult(
            clause_results=results,
            contract_risk_score=contract_score,
            contract_risk_level=contract_level,
            tokens_used=total_tokens,
            duration_ms=duration_ms,
        )

    async def _analyze_clause(
        self, cwr: ClauseWithRAG, contract_type: str
    ) -> tuple[ClauseRiskResult, int]:
        clause = cwr.clause
        match = cwr.best_match

        try:
            response = await self.chain.ainvoke({
                "contract_type": contract_type,
                "clause_type": clause.clause_type,
                "section_ref": clause.section_ref or "Unknown",
                "clause_text": clause.text[:1500],
                "similarity": f"{match.similarity_score:.0%}" if match else "N/A",
                "standard_text": match.standard_text[:800] if match else "No standard available.",
            })

            raw = response.content.strip()
            tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            data = json.loads(raw)
            score = max(0, min(100, int(data["risk_score"])))

            return ClauseRiskResult(
                clause_type=clause.clause_type,
                original_text=clause.text,
                section_ref=clause.section_ref,
                confidence=clause.confidence,
                risk_score=score,
                risk_level=data.get("risk_level", self._score_to_level(score)),
                explanation=data.get("explanation", ""),
                business_impact=data.get("business_impact", ""),
                rag_source=match.source_title if match else None,
                rag_similarity=match.similarity_score if match else None,
            ), tokens

        except Exception as e:
            logger.error(f"[{self.name}] Risk analysis failed for {clause.clause_type}: {e}")
            # Fallback: use RAG similarity as proxy for risk
            fallback_score = self._similarity_to_risk(match.similarity_score if match else 0.5)
            return ClauseRiskResult(
                clause_type=clause.clause_type,
                original_text=clause.text,
                section_ref=clause.section_ref,
                confidence=clause.confidence,
                risk_score=fallback_score,
                risk_level=self._score_to_level(fallback_score),
                explanation="Automated risk assessment based on playbook similarity.",
                business_impact="Review recommended.",
                rag_source=match.source_title if match else None,
                rag_similarity=match.similarity_score if match else None,
            ), 0

    def _compute_contract_score(self, results: list[ClauseRiskResult]) -> int:
        if not results:
            return 0
        total_weight = 0.0
        weighted_sum = 0.0
        for r in results:
            w = self.WEIGHTS.get(r.clause_type, 1.0)
            weighted_sum += r.risk_score * w
            total_weight += w
        return round(weighted_sum / total_weight) if total_weight else 0

    @staticmethod
    def _score_to_level(score: int) -> str:
        if score <= 25:
            return "low"
        if score <= 50:
            return "medium"
        if score <= 75:
            return "high"
        return "critical"

    @staticmethod
    def _similarity_to_risk(similarity: float) -> int:
        """High similarity to standard = low risk; low similarity = high risk."""
        return round((1 - similarity) * 100)
