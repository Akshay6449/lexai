# UI Walkthrough

Step-by-step guide to the LexAI web interface at **http://localhost:8000/**.

For stack and implementation details, see [Frontend](frontend.md). For first-time setup, see [Getting Started](getting-started.md).

## Before You Start

1. Backend running: `uvicorn main:app --reload --port 8000` from `backend/`
2. Database seeded: `python -m scripts.seed`
3. Open http://localhost:8000/ in a browser

## Login

The app opens on the **login** screen.

| Field | Demo value |
|-------|------------|
| Email | `admin@lexai.com` (or use quick-login chips) |
| Password | `Admin@1234` |

**Quick-login chips** fill the email for Admin, Manager, or Reviewer — password stays `Admin@1234`.

After login you land on the **Dashboard**. Your name, initials, and role appear in the sidebar footer. Use **Logout** there to sign out.

Tokens are stored in `localStorage`; refreshing the page keeps you signed in until logout or token expiry.

## Navigation

The left sidebar has two groups:

| Section | Item | Purpose |
|---------|------|---------|
| Workspace | Dashboard | Stats, charts, recent contracts and activity |
| Workspace | Upload Contract | Upload PDF/DOCX for AI analysis |
| Workspace | All Contracts | Searchable contract list with filters |
| Review | Approvals | Manager approval queue (badge shows pending count) |

The top bar includes a **search** box (filters the contract list), a **+ New Contract** shortcut to upload, and a theme toggle.

## Dashboard

What you see after login:

- **Stat cards** — contracts reviewed, high-risk count, pending approvals, AI accuracy score
- **Risk distribution** — chart of contracts by risk level
- **Monthly reviews** — contracts processed per month (stubbed chart data in dev)
- **Recent contracts** — click a row to open contract detail
- **Recent activity** — audit log feed (populated by seed demo data and logins)

Use **↺ Refresh** to reload dashboard data from the API.

## Upload Contract

1. Sidebar → **Upload Contract** (or **+ New Contract** in the header)
2. Drop a **PDF or DOCX** file (max 50MB) or click to browse
3. Set **Contract type** (NDA, MSA, SLA, Vendor, Employment)
4. Enter **Counterparty name** (optional but recommended)
5. Click **Upload & Analyze**

The UI uploads the file, runs the analysis pipeline in the background, then opens **contract detail** with live polling while status is `processing`. A toast confirms success or shows errors.

- **Remove file (✕)** — clears the selected file before upload
- **Duplicate file** — if the same file was uploaded before, you get a 409 message; open it from All Contracts or delete it first

**What happens on the server:** document extraction → clause classification → risk scoring → RAG recommendations → optional approval routing for high-risk contracts. See [AI Agents](ai-agents.md) and [Architecture — Contract status lifecycle](architecture.md#contract-status-lifecycle).

## Contract status (when does each apply?)

| Status | You see it when… |
|--------|------------------|
| **processing** | Just uploaded or **Retry Analysis** clicked; detail page polls until analysis finishes |
| **reviewed** | AI finished; risk score below 80 (default); clauses and summary populated |
| **pending_approval** | AI finished; high risk (score ≥ 80); contract appears in **Approvals → Pending** for a manager |
| **approved** | A manager clicked **Approve** on the approval queue |
| **rejected** | A manager clicked **Reject** |
| **error** | Analysis failed (e.g. network/Groq); use **Retry Analysis** after fixing connectivity |

Threshold is configurable via `RISK_APPROVAL_THRESHOLD` in `backend/.env` ([Configuration](configuration.md)).

## All Contracts

Lists every contract you can access, with:

- **Risk level** filter (low / medium / high / critical)
- **Status** filter (processing, reviewed, pending_approval, approved, rejected, error)
- **View** / **Delete** on each row (delete removes the contract and file from disk)
- **+ Upload** shortcut

Click a contract row to open **Contract detail**.

### Demo contracts (after seed)

| Contract | Status | Good for |
|----------|--------|----------|
| Acme Corp Mutual NDA | reviewed | Low-risk reviewed example |
| TechVendor MSA — Cloud Services | pending_approval | Approval workflow (manager) |
| GlobalHost SLA — Infrastructure | approved | Approved example |

Log in as **reviewer@lexai.com** to see contracts uploaded by the seed reviewer account.

## Contract Detail

Opened from the contract list, dashboard recent contracts, or after upload.

**Header** — contract name, status badge, counterparty, risk badge, and numeric risk score (0–100). **Delete** removes the contract. **Retry Analysis** appears when status is `error` or after a failed run.

While status is **processing**, a banner shows analysis in progress; the page refreshes every few seconds until clauses appear.

**Tabs:**

| Tab | Content |
|-----|---------|
| Clauses | Detected clauses with type, risk, original vs suggested text |
| Executive Summary | AI-generated summary of the contract |
| Audit Log | Actions taken on this contract |

Use **← Back to Contracts** to return to the list.

## Approvals (Manager / Admin)

Open **Approvals** from the sidebar. Pending items show a red badge on the nav item.

**Tabs:** Pending · Approved · Rejected

For each **pending** contract:

- **✓ Approve** — contract status becomes **approved**
- **✕ Reject** — contract status becomes **rejected**; optional rejection reason
- **View Analysis** — opens contract detail

**Try this flow:**

1. Log in as **manager@lexai.com** / `Admin@1234`
2. Go to **Approvals** → **Pending**
3. You should see **TechVendor MSA — Cloud Services** (seed data)
4. Approve or reject, then check **Approved** or **Rejected** tab

Reviewers can view approvals but approve/reject requires **legal_manager** or **admin** on the API; non-managers get 403 if they attempt actions.

## Role Differences

| Capability | Reviewer | Manager | Admin |
|------------|----------|---------|-------|
| Dashboard, contracts, upload | ✓ | ✓ | ✓ |
| View approvals | ✓ | ✓ | ✓ |
| Approve / reject | — | ✓ | ✓ |
| User management UI | — | — | — (API only) |

The current single-page UI does **not** include separate Playbooks or Users screens. Playbooks are managed via API and seed scripts; users via `POST /api/v1/users` (admin). See [API Reference](api-reference.md).

## Tips

- **Empty dashboard?** Run `python -m scripts.seed` and refresh.
- **401 / kicked to login?** Token expired — log in again.
- **Upload fails?** Check uvicorn logs, `GROQ_API_KEY`, and `GET http://localhost:8000/health/ai`. See [Troubleshooting](troubleshooting.md#groq--ai-analysis).
- **Analysis stuck or empty?** Hard-refresh the page; use **Retry Analysis** on the contract detail page.
- **Approvals empty?** Seed creates one pending MSA; filter **Pending** tab and log in as manager.

## Related Docs

- [Frontend](frontend.md) — template file, API wiring, customization
- [Seed Data](seed-data.md) — demo accounts and contracts
- [Authentication](authentication.md) — JWT and roles
- [Troubleshooting](troubleshooting.md) — login and UI errors
