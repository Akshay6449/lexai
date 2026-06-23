# Testing

LexAI uses **pytest** with **pytest-asyncio** for the test suite.

**Location:** `backend/tests/`

## Running Tests

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pytest tests/ -v
```

With coverage:

```powershell
pytest tests/ -v --cov=. --cov-report=term-missing
```

## Configuration

`backend/pytest.ini`:

```ini
[pytest]
pythonpath = .
asyncio_mode = auto
```

- `pythonpath = .` ensures imports like `from auth.jwt_handler import ...` resolve correctly
- `asyncio_mode = auto` handles async test functions without explicit markers in some cases

## Test Structure

**File:** `tests/test_agents.py`

| Test class | What it covers |
|------------|----------------|
| `TestDocumentExtractionAgent` | PDF stub fallback, text cleaning, chunking, section detection |
| `TestClauseClassificationAgent` | JSON parsing, invalid JSON fallback, deduplication |
| `TestRiskAnalysisAgent` | Score-to-level mapping, weighted contract score, mock LLM |
| `TestApprovalWorkflowAgent` | High-risk approval trigger, low-risk skip |
| `TestRateLimiter` | Within-limit allowance, over-limit blocking |
| `TestAuth` | bcrypt hash/verify, JWT round-trip with ephemeral RSA keys |

## Mocking Strategy

Agent tests mock the LangChain `chain.ainvoke` method to avoid real Groq API calls:

```python
with patch.object(agent.chain, "ainvoke", return_value=mock_groq_response(json_string)):
    result = await agent.run(...)
```

Auth tests generate ephemeral RSA keys in a `tmp_path` fixture.

## What Is Not Tested

- Full pipeline end-to-end (requires Groq, Qdrant, Postgres)
- API route integration tests (no `TestClient` suite yet)
- Database CRUD operations
- File upload flow

## Adding Tests

1. Create `tests/test_<module>.py`
2. Use `@pytest.mark.asyncio` for async tests
3. Mock external services (Groq, Qdrant, DB) to keep tests fast and offline

## Related Docs

- [Daily Commands](daily-commands.md) — pytest one-liner
- [AI Agents](ai-agents.md) — what agent tests cover
