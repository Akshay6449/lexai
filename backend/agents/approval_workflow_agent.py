"""
Agent 6 — Approval Workflow Agent
Evaluates contract risk score against the configured threshold.
If score > threshold: creates an Approval record and marks contract as pending_approval.
Also generates an executive summary using the LLM.
"""
import json
import logging
import time
from dataclasses import dataclass

from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langsmith import traceable

from core.config import settings
from agents.recommendation_agent import ClauseRecommendation

logger = logging.getLogger(__name__)


@dataclass
class WorkflowResult:
    requires_approval: bool
    executive_summary: str
    routing_reason: str
    tokens_used: int
    duration_ms: int


SUMMARY_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a chief legal officer writing an executive summary of a contract review.
Write a concise, professional executive summary for senior management.

Output ONLY this JSON:
{{
  "executive_summary": "<4-6 sentence executive summary covering: contract purpose, key risks found, recommended actions, and final recommendation (sign/negotiate/reject)>",
  "routing_reason": "<1-2 sentence explanation of why this contract does or does not require approval>"
}}

Tone: Professional, direct, non-technical where possible. Lead with the recommendation.
Output ONLY valid JSON.
"""),
    ("human", """Contract: {contract_name}
Type: {contract_type}
Counterparty: {counterparty}
Overall Risk Score: {risk_score}/100 ({risk_level})
Approval Threshold: {threshold}

HIGH/CRITICAL RISK CLAUSES:
{risk_clauses}

KEY RECOMMENDATIONS:
{recommendations}

Write the executive summary JSON:"""),
])


class ApprovalWorkflowAgent:
    name = "ApprovalWorkflowAgent"

    def __init__(self):
        self.llm = ChatGroq(
            model=settings.GROQ_MODEL,
            temperature=0.3,
            max_tokens=800,
            api_key=settings.GROQ_API_KEY,
        )
        self.chain = SUMMARY_PROMPT | self.llm
        self.threshold = settings.RISK_APPROVAL_THRESHOLD

    @traceable(name="ApprovalWorkflowAgent.run")
    async def run(
        self,
        contract_name: str,
        contract_type: str,
        counterparty: str,
        risk_score: int,
        risk_level: str,
        recommendations: list[ClauseRecommendation],
    ) -> WorkflowResult:
        t0 = time.perf_counter()

        risk_score = 0 if risk_score is None else int(risk_score)
        risk_level = risk_level or "low"
        requires_approval = risk_score >= self.threshold
        summary_data, tokens = await self._generate_summary(
            contract_name, contract_type, counterparty,
            risk_score, risk_level, recommendations, requires_approval
        )

        duration_ms = round((time.perf_counter() - t0) * 1000)
        logger.info(
            f"[{self.name}] Contract '{contract_name}' score={risk_score} "
            f"threshold={self.threshold} requires_approval={requires_approval} | {duration_ms}ms"
        )

        return WorkflowResult(
            requires_approval=requires_approval,
            executive_summary=summary_data.get("executive_summary", ""),
            routing_reason=summary_data.get("routing_reason", ""),
            tokens_used=tokens,
            duration_ms=duration_ms,
        )

    async def _generate_summary(
        self,
        contract_name: str,
        contract_type: str,
        counterparty: str,
        risk_score: int,
        risk_level: str,
        recommendations: list[ClauseRecommendation],
        requires_approval: bool,
    ) -> tuple[dict, int]:
        # Summarize high/critical clauses for the prompt
        high_risk = [r for r in recommendations if (r.risk_score or 0) >= 51]
        risk_clauses_text = "\n".join(
            f"- {r.clause_type.upper()} (score {r.risk_score}): {r.why_risky}"
            for r in high_risk[:5]
        ) or "None identified."

        rec_text = "\n".join(
            f"- {r.clause_type.upper()}: {r.negotiation_points[0] if r.negotiation_points else 'Review recommended.'}"
            for r in high_risk[:5]
        ) or "No critical recommendations."

        try:
            response = await self.chain.ainvoke({
                "contract_name": contract_name,
                "contract_type": contract_type,
                "counterparty": counterparty or "Unknown",
                "risk_score": risk_score,
                "risk_level": risk_level,
                "threshold": self.threshold,
                "risk_clauses": risk_clauses_text,
                "recommendations": rec_text,
            })

            raw = response.content.strip()
            tokens = response.usage_metadata.get("total_tokens", 0) if response.usage_metadata else 0

            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]

            return json.loads(raw), tokens

        except Exception as e:
            logger.error(f"[{self.name}] Summary generation failed: {e}")
            verdict = "requires immediate legal manager approval" if requires_approval else "can proceed to execution"
            return {
                "executive_summary": (
                    f"This {contract_type} with {counterparty or 'counterparty'} received a risk score "
                    f"of {risk_score}/100 ({risk_level} risk). {len(high_risk)} high or critical risk "
                    f"clauses were identified. The contract {verdict}."
                ),
                "routing_reason": (
                    f"Risk score {risk_score} {'exceeds' if requires_approval else 'is below'} "
                    f"the approval threshold of {self.threshold}."
                ),
            }, 0
