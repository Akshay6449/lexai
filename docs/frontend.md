# Frontend

LexAI ships a single-page web UI served directly by FastAPI at the root path.

**File:** `backend/templates/contract-review-platform.html`
**URL:** http://localhost:8000/

There is also a standalone `frontend/` directory used for Docker builds, but local development serves the template from the backend.

## Technology

- HTML5 + CSS3 + Tailwind CSS (CDN)
- Vanilla JavaScript (no React/Vue build step)
- Jinja2 template rendered by FastAPI

## Pages / Views

The UI is a single HTML file with client-side view switching:

| View | Description |
|------|-------------|
| Login | Email/password form with quick-login buttons |
| Dashboard | Stats cards, risk chart, recent activity |
| Upload Contract | PDF/DOCX upload and analysis trigger |
| All Contracts | Contract list with risk/status filters; View and Delete per row |
| Contract detail | Clause analysis, executive summary, audit log; polling while `processing`; Retry Analysis on `error`; Delete |
| Approvals | Pending approval queue with approve/reject (manager+) |

Navigation is handled via JavaScript showing/hiding DOM sections.

For a screen-by-screen tour with demo data, see [UI Walkthrough](ui-walkthrough.md).

**Note:** Playbooks and user management are API-only in the current UI — no dedicated nav screens.

## API Integration

### Base URL

```javascript
const API = '/api/v1';
```

All API calls use relative paths against the same origin (port 8000).

### Authentication

1. User submits login form → `POST /api/v1/auth/login`
2. Access and refresh tokens stored in `localStorage`:
   - `lexai_token` — access token
   - `lexai_refresh` — refresh token
3. Subsequent requests include header:

```javascript
headers: { 'Authorization': 'Bearer ' + localStorage.getItem('lexai_token') }
```

4. On 401, the UI attempts token refresh via `POST /api/v1/auth/refresh`

### Quick Login Buttons

The login page provides one-click email fill for demo accounts:

| Button | Email |
|--------|-------|
| Admin | admin@lexai.com |
| Manager | manager@lexai.com |
| Reviewer | reviewer@lexai.com |

Password defaults to `Admin@1234` for all quick-login buttons.

## Key UI Features

- **Contract upload** — drag-and-drop or file picker (PDF/DOCX)
- **Risk dashboard** — color-coded risk levels (low/medium/high/critical)
- **Clause viewer** — side-by-side original vs. suggested text
- **Approval actions** — approve/reject buttons for managers
- **Toast notifications** — success/error feedback

## Serving the UI

In `backend/main.py`:

```python
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    return templates.TemplateResponse(request, "contract-review-platform.html")
```

**Note:** Starlette 1.x requires `request` as the first argument to `TemplateResponse`.

## Customization

To modify the UI:

1. Edit `backend/templates/contract-review-platform.html`
2. Restart uvicorn (or rely on `--reload` for Python changes; HTML is read per request)

Styles use Tailwind utility classes and CSS custom properties for theming (dark professional legal aesthetic).

## Related Docs

- [UI Walkthrough](ui-walkthrough.md) — screen-by-screen guide
- [API Reference](api-reference.md) — endpoints the UI calls
- [Authentication](authentication.md) — login flow
- [Getting Started](getting-started.md) — access the UI locally
