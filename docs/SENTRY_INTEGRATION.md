## Sentry Error Monitoring & Performance — Integration Documentation (Docs‑Only)

This guide documents how to add Sentry to MAMS for backend (FastAPI) and frontend (Next.js) error tracking and performance monitoring. It specifies configuration, instrumentation targets, testing, and rollout for later implementation.

### Official documentation (verify before implementing)
- Sentry Platforms index: `https://docs.sentry.io/platforms/`
- Python FastAPI guide: `https://docs.sentry.io/platforms/python/guides/fastapi/`
- Python performance/profiling: `https://docs.sentry.io/platforms/python/performance/`
- Next.js guide: `https://docs.sentry.io/platforms/javascript/guides/nextjs/`
- Releases & source maps: `https://docs.sentry.io/platforms/javascript/guides/nextjs/manual-setup/`


### 1) What We Want
- Automatic capture of unhandled exceptions in backend and frontend
- Manual capture for domain errors (validation, provider faults)
- Server and browser performance data (traces, spans), with controllable sampling
- Release, environment, and commit metadata for accurate regression tracking


### 2) Prerequisites
- Sentry account, organization, and projects:
  - One project for backend (Python/FastAPI)
  - One project for frontend (Next.js)
- Obtain DSNs from each project settings
- (Optional) Auth token for release uploads / source maps


### 3) Configuration (Environment templates)
Add placeholders to the root and app‑specific `.env` files (align names with your config loader):
```
# Common
SENTRY_ENV=development            # development|staging|production
SENTRY_RELEASE=auto               # set to Git SHA or version tag at build

# Backend
SENTRY_DSN_BACKEND=
SENTRY_TRACES_SAMPLE_RATE_BACKEND=0.2    # performance sampling
SENTRY_PROFILES_SAMPLE_RATE_BACKEND=0.0  # set >0 to enable profiling
SENTRY_SEND_DEFAULT_PII=false

# Frontend
SENTRY_DSN_FRONTEND=
SENTRY_TRACES_SAMPLE_RATE_FRONTEND=0.2

# (Optional) For uploads from CI
SENTRY_AUTH_TOKEN=
SENTRY_ORG=your-org
SENTRY_PROJECT_FRONTEND=frontend
SENTRY_PROJECT_BACKEND=backend
```

Sampling guidance:
- Dev: traces 1.0 (full), prod: 0.05–0.3 depending on traffic
- Profiles add overhead; enable selectively


### 4) Backend (FastAPI) Instrumentation Plan (to implement later)
- Install: `pip install 'sentry-sdk[fastapi]'`
- Initialize at app startup (before routes mount):
  - `dsn=SENTRY_DSN_BACKEND`
  - `environment=SENTRY_ENV`
  - `release=SENTRY_RELEASE`
  - `traces_sample_rate=SENTRY_TRACES_SAMPLE_RATE_BACKEND`
  - `profiles_sample_rate=SENTRY_PROFILES_SAMPLE_RATE_BACKEND`
  - `send_default_pii=SENTRY_SEND_DEFAULT_PII` (keep false unless required)
- Capture exceptions via middleware automatically
- Manual capture in known error sites:
  - Provider timeouts, DB errors, SSE failures
  - Add breadcrumbs for negotiation_id, session_id for correlation
- Performance:
  - Annotate spans around LLM calls and DB ops for latency hotspots

Pseudocode (reference only; not actual code):
```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

def init_sentry():
    sentry_sdk.init(
        dsn=os.environ.get("SENTRY_DSN_BACKEND"),
        environment=os.environ.get("SENTRY_ENV", "development"),
        release=os.environ.get("SENTRY_RELEASE", "dev"),
        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE_BACKEND", "0.2")),
        profiles_sample_rate=float(os.environ.get("SENTRY_PROFILES_SAMPLE_RATE_BACKEND", "0.0")),
        send_default_pii=os.environ.get("SENTRY_SEND_DEFAULT_PII", "false").lower() == "true",
        integrations=[FastApiIntegration()],
    )
```


### 5) Frontend (Next.js) Instrumentation Plan (to implement later)
- Install: `npm i @sentry/nextjs` (or `pnpm`/`yarn`)
- Initialize with the wizard or manual setup per docs:
  - `SENTRY_DSN_FRONTEND`, `SENTRY_ENV`, `SENTRY_RELEASE`
  - `tracesSampleRate=SENTRY_TRACES_SAMPLE_RATE_FRONTEND`
- Enable source maps (CI upload token + release/version)
- Add route instrumentation if using app router for better spans

Example config references (see official Next.js guide):
- `sentry.client.config.ts` / `sentry.edge.config.ts` / `sentry.server.config.ts`
- `next.config.js` Sentry plugin (for build‑time settings)


### 6) Data Hygiene & PII
- Keep `send_default_pii=false` on backend unless business/legal requires otherwise
- Scrub sensitive fields (API keys, auth tokens, DSNs, emails) from contexts
- Avoid logging full prompts/responses; attach short hashes or redacted snippets
- Use Sentry’s server‑side scrubbing settings for additional safety


### 7) Testing Strategy (after implementation)
- Backend:
  - Force an exception in a test endpoint; verify event in Sentry
  - Simulate provider timeout; assert captured with breadcrumbs
  - Verify transaction traces around LLM/DB spans
- Frontend:
  - Trigger a client error; verify appearance in Sentry frontend project
  - Confirm source maps link to readable stack traces
- Load/overhead:
  - Validate acceptable overhead with sampling (document baseline latency)


### 8) Alerts & Workflow
- Configure alert rules for:
  - New issue spike, error rate thresholds, release regressions
  - Performance: p95/p99 latency regression
- Set ownership rules to route issues to the correct team
- Connect Sentry to Slack/Jira for triage


### 9) Troubleshooting
- No events:
  - Verify DSN, network egress, and that SDK init runs before app use
  - Check sampling rates (might be 0.0)
- Missing stack traces / minified code (frontend):
  - Ensure source maps are uploaded and `release` matches build
- Duplicate events:
  - Avoid double initialization (e.g., dev HMR); guard init


### 10) Cost & Usage Considerations
- Control volume with sampling; use environments to separate dev/staging/prod
- Reduce noise with inbound data filters and issue fingerprinting
- Limit extra context fields to essentials


### 11) Rollout Checklist (Docs‑Only)
- [ ] Backend project/DSN configured; init at app start
- [ ] Frontend project/DSN configured; init via `@sentry/nextjs`
- [ ] Sampling and profiling rates agreed per environment
- [ ] Source maps upload automated in CI with `SENTRY_AUTH_TOKEN`
- [ ] Alerts/ownership rules configured


