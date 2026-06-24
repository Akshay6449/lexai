# API Reference

Base URL: `http://localhost:8000/api/v1`

Interactive documentation: **http://localhost:8000/docs** (Swagger UI)

## Authentication

Most endpoints require a Bearer token:

```
Authorization: Bearer <access_token>
```

Obtain a token via `POST /api/v1/auth/login`. See [Authentication](authentication.md).

## Auth — `/api/v1/auth`

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/login` | None | Email + password → access and refresh tokens |
| POST | `/refresh` | None | Refresh token → new token pair |
| GET | `/me` | Bearer | Current user profile |
| POST | `/logout` | Bearer | Logout (audit log entry) |

### Login request

```json
{
  "email": "admin@lexai.com",
  "password": "Admin@1234"
}
```

### Login response

```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Users — `/api/v1/users`

**Role required:** Admin

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List all users |
| POST | `/` | Create user |
| PATCH | `/{user_id}` | Update user (name, role, active status) |
| DELETE | `/{user_id}` | Delete user (cannot delete self) |

## Contracts — `/api/v1/contracts`

**Role required:** Any legal role

| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Upload PDF/DOCX contract (multipart form); status → `processing` |
| GET | `/` | List contracts (newest first); query: `status`, `risk_level`, `contract_type` |
| GET | `/{contract_id}` | Contract detail |
| POST | `/{contract_id}/analyze` | Re-run AI pipeline (clears clauses, status → `processing`) |
| DELETE | `/{contract_id}` | Delete contract and file (uploader or admin only) |

### Upload form fields

| Field | Type | Required |
|-------|------|----------|
| `file` | file | Yes |
| `contract_type` | string | Yes (NDA, MSA, SLA, Vendor, Employment) |
| `counterparty` | string | No |
| `playbook` | string | No |

Upload triggers the AI pipeline in the background. On success the contract is `processing` until the pipeline sets `reviewed`, `pending_approval`, or `error`. See [Architecture — Contract status lifecycle](architecture.md#contract-status-lifecycle).

## Analysis — `/api/v1/analysis`

**Role required:** Any legal role

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{contract_id}/clauses` | Classified clauses with risk and RAG data |
| GET | `/{contract_id}/risk` | Contract-level risk breakdown |
| GET | `/{contract_id}/audit` | Audit trail for this contract |
| GET | `/{contract_id}/summary` | Executive summary text |

## Approvals — `/api/v1/approvals`

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/` | Manager+ | List all approvals |
| GET | `/pending` | Manager+ | Pending approvals only |
| POST | `/{approval_id}/approve` | Manager+ | Approve contract |
| POST | `/{approval_id}/reject` | Manager+ | Reject contract |
| POST | `/{approval_id}/request-changes` | Manager+ | Request changes with notes |

## Playbooks — `/api/v1/playbooks`

| Method | Path | Role | Description |
|--------|------|------|-------------|
| GET | `/` | Any legal | List playbooks |
| POST | `/` | Manager+ | Create playbook |
| POST | `/{playbook_id}/sync` | Manager+ | Sync playbook to Qdrant |
| GET | `/qdrant/stats` | Any legal | Qdrant collection statistics |

## Dashboard — `/api/v1/dashboard`

**Role required:** Any legal role

| Method | Path | Description |
|--------|------|-------------|
| GET | `/stats` | Contract counts, high-risk count, pending approvals |
| GET | `/risk-distribution` | Count by risk level (low/medium/high/critical) |
| GET | `/monthly-reviews` | Monthly review chart data |
| GET | `/recent-activity` | Recent audit log entries |

## Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | `{"status":"ok","version":"1.0.0","service":"lexai-api"}` |
| GET | `/health/ai` | None | Groq API reachability check (5s timeout); `{"groq":"ok"|"error","detail":"..."}` |

Use `/health/ai` to verify the backend can reach Groq before debugging failed contract analysis. See [Troubleshooting — Groq / AI analysis](troubleshooting.md#groq--ai-analysis).

## Error Responses

Standard FastAPI error format:

```json
{
  "detail": "Human-readable error message"
}
```

| Status | Meaning |
|--------|---------|
| 400 | Bad request / validation error |
| 401 | Invalid or missing token |
| 403 | Insufficient role permissions |
| 404 | Resource not found |
| 409 | Conflict (e.g. duplicate email) |
| 429 | Rate limit exceeded |

## Related Docs

- [Authentication](authentication.md) — token flow and roles
- [Frontend](frontend.md) — how the UI calls these endpoints
