"""
LexAI Test Suite
Run: pytest backend/tests/ -v --cov=backend --cov-report=html
"""
import asyncio
import json
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport


# ── Fixtures ─────────────────────────────────────────────────

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_groq_response():
    """Mock a Groq LLM response object."""
    def _make(content: str, tokens: int = 250):
        mock = MagicMock()
        mock.content = content
        mock.usage_metadata = {"total_tokens": tokens}
        return mock
    return _make


# ── Agent 1: Document Extraction ─────────────────────────────

class TestDocumentExtractionAgent:

    @pytest.mark.asyncio
    async def test_extract_stub_fallback(self, tmp_path):
        """Falls back to stub text when PyMuPDF not installed."""
        from agents.document_extraction_agent import DocumentExtractionAgent
        agent = DocumentExtractionAgent()
        # Create a dummy file
        dummy = tmp_path / "test.pdf"
        dummy.write_bytes(b"%PDF-1.4 stub")
        result = await agent.run(str(dummy))
        assert result.raw_text
        assert len(result.chunks) > 0
        assert result.file_type == "pdf"

    def test_clean_text(self):
        from agents.document_extraction_agent import DocumentExtractionAgent
        agent = DocumentExtractionAgent()
        dirty = "Hello\r\n\r\n\r\nWorld   spaces\x00null"
        clean = agent._clean_text(dirty)
        assert "\r" not in clean
        assert "\x00" not in clean
        assert "   " not in clean

    def test_chunking_respects_size(self):
        from agents.document_extraction_agent import DocumentExtractionAgent, CHUNK_SIZE
        agent = DocumentExtractionAgent()
        text = "A" * (CHUNK_SIZE * 3)
        chunks = agent._chunk_text(text)
        assert len(chunks) >= 3
        for chunk in chunks:
            assert len(chunk.text) <= CHUNK_SIZE + 50  # small tolerance for boundary

    def test_detect_section(self):
        from agents.document_extraction_agent import DocumentExtractionAgent
        agent = DocumentExtractionAgent()
        assert agent._detect_section("8.2. Liability Clause\nText...") == "Section 8.2"
        assert agent._detect_section("No section here") is None


# ── Agent 2: Clause Classification ───────────────────────────

class TestClauseClassificationAgent:

    @pytest.mark.asyncio
    async def test_classify_parses_valid_json(self, mock_groq_response):
        from agents.clause_classification_agent import ClauseClassificationAgent
        from agents.document_extraction_agent import DocumentChunk

        valid_response = json.dumps({
            "clauses": [
                {
                    "clause_type": "liability",
                    "text": "Neither party shall be liable for...",
                    "section_ref": "Section 8",
                    "confidence": 0.97,
                    "chunk_index": 0,
                }
            ]
        })

        agent = ClauseClassificationAgent()
        with patch.object(agent.chain, "ainvoke", return_value=mock_groq_response(valid_response)):
            chunks = [DocumentChunk(0, "Neither party shall be liable for damages.", 0, 50)]
            clauses, tokens = await agent.run(chunks, "NDA")

        assert len(clauses) == 1
        assert clauses[0].clause_type == "liability"
        assert clauses[0].confidence == 0.97

    @pytest.mark.asyncio
    async def test_classify_handles_invalid_json(self, mock_groq_response):
        from agents.clause_classification_agent import ClauseClassificationAgent
        from agents.document_extraction_agent import DocumentChunk

        agent = ClauseClassificationAgent()
        with patch.object(agent.chain, "ainvoke", return_value=mock_groq_response("not json")):
            chunks = [DocumentChunk(0, "Some text.", 0, 10)]
            clauses, tokens = await agent.run(chunks, "NDA")

        assert clauses == []     # graceful fallback

    def test_deduplication(self):
        from agents.clause_classification_agent import ClauseClassificationAgent, ClassifiedClause
        agent = ClauseClassificationAgent()
        clauses = [
            ClassifiedClause("liability", "Text A...", None, 0.9, 0),
            ClassifiedClause("liability", "Text A...", None, 0.8, 1),   # duplicate
            ClassifiedClause("termination", "Text B...", None, 0.85, 2),
        ]
        deduped = agent._deduplicate(clauses)
        types = [c.clause_type for c in deduped]
        assert types.count("liability") == 1
        assert "termination" in types


# ── Agent 4: Risk Analysis ────────────────────────────────────

class TestRiskAnalysisAgent:

    def test_score_to_level(self):
        from agents.risk_analysis_agent import RiskAnalysisAgent
        assert RiskAnalysisAgent._score_to_level(10) == "low"
        assert RiskAnalysisAgent._score_to_level(40) == "medium"
        assert RiskAnalysisAgent._score_to_level(65) == "high"
        assert RiskAnalysisAgent._score_to_level(85) == "critical"

    def test_weighted_score_computation(self):
        from agents.risk_analysis_agent import RiskAnalysisAgent, ClauseRiskResult
        agent = RiskAnalysisAgent()
        results = [
            ClauseRiskResult("indemnification", "text", None, 0.9, 90, "critical", "", "", None, None),
            ClauseRiskResult("governing_law", "text", None, 0.9, 10, "low", "", "", None, None),
        ]
        score = agent._compute_contract_score(results)
        # indemnification weight=1.5, governing_law weight=0.5
        # (90*1.5 + 10*0.5) / (1.5 + 0.5) = (135 + 5) / 2.0 = 70
        assert score == 70

    @pytest.mark.asyncio
    async def test_risk_analysis_with_mock(self, mock_groq_response):
        from agents.risk_analysis_agent import RiskAnalysisAgent
        from agents.clause_classification_agent import ClassifiedClause
        from agents.rag_retrieval_agent import ClauseWithRAG, RAGMatch

        risk_json = json.dumps({
            "risk_score": 82,
            "risk_level": "critical",
            "explanation": "Unlimited liability carve-out is non-standard.",
            "business_impact": "Potential uncapped exposure.",
        })

        agent = RiskAnalysisAgent()
        with patch.object(agent.chain, "ainvoke", return_value=mock_groq_response(risk_json)):
            clause = ClassifiedClause("liability", "UNLIMITED liability...", "Section 8", 0.95, 0)
            match = RAGMatch("liability", "NDA Standard", "Playbook §4.3", "Standard text...", 0.94, "v1")
            cwr = ClauseWithRAG(clause=clause, best_match=match, all_matches=[match])

            result = await agent.run([cwr], "NDA")

        assert result.clause_results[0].risk_score == 82
        assert result.clause_results[0].risk_level == "critical"
        assert result.contract_risk_score > 0


# ── Agent 6: Approval Workflow ────────────────────────────────

class TestApprovalWorkflowAgent:

    @pytest.mark.asyncio
    async def test_high_risk_triggers_approval(self, mock_groq_response):
        from agents.approval_workflow_agent import ApprovalWorkflowAgent

        summary_json = json.dumps({
            "executive_summary": "Contract has critical risk and requires approval.",
            "routing_reason": "Risk score 85 exceeds threshold of 80.",
        })

        agent = ApprovalWorkflowAgent()
        with patch.object(agent.chain, "ainvoke", return_value=mock_groq_response(summary_json)):
            result = await agent.run("Acme NDA", "NDA", "Acme Corp", 85, "critical", [])

        assert result.requires_approval is True
        assert "approval" in result.routing_reason.lower()

    @pytest.mark.asyncio
    async def test_low_risk_skips_approval(self, mock_groq_response):
        from agents.approval_workflow_agent import ApprovalWorkflowAgent

        summary_json = json.dumps({
            "executive_summary": "Contract is within acceptable parameters.",
            "routing_reason": "Risk score 30 is below threshold of 80.",
        })

        agent = ApprovalWorkflowAgent()
        with patch.object(agent.chain, "ainvoke", return_value=mock_groq_response(summary_json)):
            result = await agent.run("Simple NDA", "NDA", "Acme Corp", 30, "low", [])

        assert result.requires_approval is False


# ── Rate Limiter ──────────────────────────────────────────────

class TestRateLimiter:

    @pytest.mark.asyncio
    async def test_allows_within_limit(self):
        from core.rate_limiter import RateLimiter
        limiter = RateLimiter(requests_per_minute=5)
        for _ in range(5):
            assert await limiter.is_allowed("test-ip") is True

    @pytest.mark.asyncio
    async def test_blocks_over_limit(self):
        from core.rate_limiter import RateLimiter
        limiter = RateLimiter(requests_per_minute=3)
        for _ in range(3):
            await limiter.is_allowed("blocked-ip")
        result = await limiter.is_allowed("blocked-ip")
        assert result is False


# ── Auth ──────────────────────────────────────────────────────

class TestAuth:

    def test_password_hash_and_verify(self):
        from auth.jwt_handler import hash_password, verify_password
        hashed = hash_password("MySecret123!")
        assert verify_password("MySecret123!", hashed)
        assert not verify_password("WrongPassword", hashed)

    def test_token_round_trip(self, tmp_path):
        """Generate RSA keys and verify JWT round-trip."""
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.primitives import serialization
        from auth.jwt_handler import create_access_token, decode_token
        import os

        # Generate ephemeral RSA key pair
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        priv_pem = private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        ).decode()
        pub_pem = private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode()

        priv_path = tmp_path / "private.pem"
        pub_path = tmp_path / "public.pem"
        priv_path.write_text(priv_pem)
        pub_path.write_text(pub_pem)

        with patch("auth.jwt_handler.settings") as mock_settings:
            mock_settings.JWT_PRIVATE_KEY_PATH = str(priv_path)
            mock_settings.JWT_PUBLIC_KEY_PATH = str(pub_path)
            mock_settings.JWT_ALGORITHM = "RS256"
            mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 60

            token = create_access_token("user-123", "legal_manager", "test@lexai.com")
            payload = decode_token(token)

        assert payload["sub"] == "user-123"
        assert payload["role"] == "legal_manager"
        assert payload["type"] == "access"
