# Overview

## What is LexAI?

LexAI is an enterprise contract intelligence platform that uses AI to automate legal contract review. It extracts text from PDF and DOCX files, classifies clauses, compares them against standard playbooks via RAG, scores risk, and routes high-risk contracts for manager approval.

## Problem Statement

Enterprise legal teams review hundreds of contracts manually. This process is:

- **Slow** — each contract can take hours of attorney time
- **Inconsistent** — different reviewers apply different standards
- **Risky** — non-standard or dangerous clauses can be missed under deadline pressure

LexAI automates the repetitive analysis so legal professionals can focus on judgment, negotiation, and approval decisions.

## Primary Use Case

```
Upload contract → AI pipeline analyzes → Review dashboard → Approve if high risk
```

1. A **Legal Reviewer** uploads a PDF or DOCX contract.
2. The **6-agent pipeline** extracts text, classifies clauses, retrieves playbook matches, scores risk, and generates recommendations.
3. Results appear on the **dashboard** with clause-level detail and an executive summary.
4. If the contract risk score exceeds the threshold (default 80), an **approval workflow** routes it to a Legal Manager.

## Target Users

| Role | Who | Primary goals |
|------|-----|---------------|
| **Legal Reviewer** | Junior/mid attorneys, paralegals | Upload contracts, review AI findings |
| **Legal Manager** | Senior counsel, legal ops leads | Approve/reject high-risk deals, manage playbooks |
| **Admin** | Platform administrator | User management, system configuration |

## Roles and Permissions

| Permission | Legal Reviewer | Legal Manager | Admin |
|-----------|:--------------:|:-------------:|:-----:|
| Upload contracts | Yes | Yes | Yes |
| View analysis | Yes | Yes | Yes |
| Comment on clauses | Yes | Yes | Yes |
| Approve / Reject | No | Yes | Yes |
| Manage users | No | No | Yes |
| Manage playbooks | No | Yes | Yes |
| View audit logs | No | Yes | Yes |
| System config | No | No | Yes |

## Supported Contract Types

- NDA (Non-Disclosure Agreement)
- MSA (Master Services Agreement)
- SLA (Service Level Agreement)
- Vendor
- Employment

## Clause Types Analyzed

The classification agent identifies eight clause categories:

- Confidentiality
- Liability
- Indemnification
- Termination
- Payment
- Data privacy
- Intellectual property
- Governing law

## Technology Approach

LexAI separates concerns across three layers:

- **PostgreSQL** — users, contracts, approvals, playbook text, audit logs (relational, ACID)
- **Qdrant** — semantic search over playbook clause embeddings (RAG grounding)
- **LangGraph pipeline** — six specialized agents orchestrated with shared state (extract → classify → retrieve → risk → recommend → approve)

Groq powers LLM steps; LangSmith tracing is optional for debugging. For the full rationale behind each choice and alternatives considered, see **[Design Rationale](design-rationale.md)**.

## Next Steps

- [Design Rationale](design-rationale.md) — why this stack and architecture
- [Architecture](architecture.md) — how the system is built
- [Getting Started](getting-started.md) — run it locally
