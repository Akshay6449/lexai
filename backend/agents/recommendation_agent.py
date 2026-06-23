"""
Agent 5 — Recommendation Agent
For each high/critical risk clause, generates:
  - A suggested replacement clause
  - Plain-English explanation
  - Business impact assessment
  - Negotiation talking points
Only processes clauses above a minimum risk threshold to save tokens.
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
from agents.risk_analysis_agent import ClauseRiskResult

logger = logging.getLogger(__name__)

# Only generate recommendations for clauses above this threshold
RECOMMENDATION_THRESHOLD = 25


@dataclass
class ClauseRecommendation:
    clause_type: str
    original_text: str
    suggested_text: str
    explanation: str
    why_risky: str
    business_impact: str
    negotiation_points: list[str]
    risk_score: int
    risk_level: str
    section_ref: Optional[str]
    rag_source: Optional[str]


RECOMMENDATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a senior corporate attorney drafting contract redlines.
Your task is to rewrite a problematic contract clause to protect the company's interests.

Output ONLY this JSON structure:
{{
  "suggested_text": "<complete rewritten clause text, ready for insertion into the contract>",
  "explanation": "<plain-English explanation of what this clause means, 2-3 sentences>",
  "why_risky": "<specific legal risk in current version, 2-3 sentences>",
  "business_impact": "<financial/operational business impact if accepted as-is, 1-2 sentences>",
  "negotiation_points": ["<point 1>", "<point 2>", "<point 3>"]
}}

Guidelines for suggested_text:
- Write in formal legal language consistent with the contract type
- Keep the clause's original intent but add protective language
- Include specific caps, timeframes, and carve-outs where appropriate
- Make it mutual and fair where possible
- Reference industry standards (e.g., "not to exceed 12 months of fees")

Output ONLY valid JSON.
"""),
    ("human", """Contract type: {contract_type}
Clause type: {clause_type}
Risk score: {risk_score}/100 ({risk_level})
Section: {section_ref}

CURRENT PROBLEMATIC CLAUSE:
{original_text}

PLAYBOOK STANDARD FOR REFERENCE:
{standard_text}

Draft the improved clause and return JSON:"""),
])


class RecommendationAgent:
    name = "RecommendationAgent"

    def __init__(self):
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=0.2,
            max_tokens=1500,
            api_key=settings.GROQ_API_KEY,
        )
        self.chain = RECOMMENDATION_PROMPT | self.llm

    @traceable(name="RecommendationAgent.run")
    async def run(
        self,
        clause_results: list[ClauseRiskResult],
        contract_type: str,
        rag_matches: dict,          # clause_type -> standard_text
    ) -> tuple[list[ClauseRecommendation], int]:
        """
        Returns (recommendations, total_tokens).
        Only processes clauses above RECOMMENDATION_THRESHOLD.
        """
        t0 = time.perf_counter()
        recommendations: list[ClauseRecommendation] = []
        total_tokens = 0

        for result in clause_results:
            if result.risk_score < RECOMMENDATION_THRESHOLD:
                # Low risk — pass through with minimal suggestion
                recommendations.append(self._low_risk_passthrough(result))
                continue

            rec, tokens = await self._generate_recommendation(
                result, contract_type,
                rag_matches.get(result.clause_type, "Standard clause per company policy.")
            )
            recommendations.append(rec)
            total_tokens += tokens

        duration_ms = round((time.perf_counter() - t0) * 1000)
        logger.info(
            f"[{self.name}] Generated {len(recommendations)} recommendations "
            f"in {duration_ms}ms ({total_tokens} tokens)"
        )
        return recommendations, total_tokens

    async def _generate_recommendation(
        self,
        result: ClauseRiskResult,
        contract_type: str,
        standard_text: str,
    ) -> tuple[ClauseRecommendation, int]:
        try:
            response = await self.chain.ainvoke({
                "contract_type": contract_type,
                "clause_type": result.clause_type,
                "risk_score": result.risk_score,
                "risk_level": result.risk_level,
                "section_ref": result.section_ref or "Unknown",
                "original_text": result.original_text[:1200],
                "standard_text": standard_text[:600],
            })

            raw = response.content.strip()
            tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            data = json.loads(raw)

            return ClauseRecommendation(
                clause_type=result.clause_type,
                original_text=result.original_text,
                suggested_text=data.get("suggested_text", ""),
                explanation=data.get("explanation", result.explanation),
                why_risky=data.get("why_risky", result.explanation),
                business_impact=data.get("business_impact", result.business_impact),
                negotiation_points=data.get("negotiation_points", []),
                risk_score=result.risk_score,
                risk_level=result.risk_level,
                section_ref=result.section_ref,
                rag_source=result.rag_source,
            ), tokens

        except Exception as e:
            logger.error(f"[{self.name}] Recommendation failed for {result.clause_type}: {e}")
            return self._fallback_recommendation(result, standard_text), 0

    def _low_risk_passthrough(self, result: ClauseRiskResult) -> ClauseRecommendation:
        return ClauseRecommendation(
            clause_type=result.clause_type,
            original_text=result.original_text,
            suggested_text=result.original_text,  # no change needed
            explanation=result.explanation or "This clause is within acceptable parameters.",
            why_risky="Low risk — no significant concerns identified.",
            business_impact="Minimal business impact. Clause is standard or better than playbook.",
            negotiation_points=["Clause is acceptable as-is."],
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            section_ref=result.section_ref,
            rag_source=result.rag_source,
        )

    def _fallback_recommendation(
        self, result: ClauseRiskResult, standard_text: str
    ) -> ClauseRecommendation:
        return ClauseRecommendation(
            clause_type=result.clause_type,
            original_text=result.original_text,
            suggested_text=standard_text,
            explanation=result.explanation or "Risk detected in this clause.",
            why_risky=result.explanation or "Deviates from company standard.",
            business_impact=result.business_impact or "Review required before execution.",
            negotiation_points=[
                "Request alignment with company standard playbook.",
                "Insist on mutual caps and time-limited obligations.",
                "Escalate to legal counsel if counterparty refuses.",
            ],
            risk_score=result.risk_score,
            risk_level=result.risk_level,
            section_ref=result.section_ref,
            rag_source=result.rag_source,
        )
