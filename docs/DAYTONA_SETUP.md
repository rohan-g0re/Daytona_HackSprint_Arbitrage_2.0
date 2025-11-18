## Daytona Setup — Sandboxes for Running AI-Generated Code (Docs‑Only)

This guide documents how to use Daytona to run untrusted/AI‑generated code safely in isolated sandboxes and how to connect it to MAMS for evaluation workflows. It specifies configuration, SDK usage patterns, and rollout steps for later implementation.

Official reference:
- Daytona site (View Docs from navbar): https://www.daytona.io/

The site shows Python SDK usage and core capabilities (create sandboxes, execute code with real‑time output, file operations, Git, LSP). Always consult the “View Docs” link on the site for the most current API details.


### 1) What We Want
- Safely execute AI‑generated code (evals, small utilities) in Daytona sandboxes, isolated from local infrastructure
- Real‑time output streaming for long‑running commands
- File upload/download to/from sandbox for datasets and artifacts
- Clean creation/removal lifecycle per negotiation experiment or batch job


### 2) Prerequisites
- Python 3.9+ environment (Windows ARM dev machine supported for client usage)
- Daytona Python SDK installed:
```
pip install daytona
```
- Network access to Daytona’s service (per your account/plan)


### 3) Configuration (App‑internal toggles)
Add these toggles to your app’s env/config (these are internal to MAMS; verify any required Daytona auth variables from the official docs before implementation):
```
DAYTONA_ENABLED=true
DAYTONA_DEFAULT_LANGUAGE=python
DAYTONA_SANDBOX_TTL_MINUTES=30
DAYTONA_MAX_PARALLEL_SANDBOXES=8
```
Notes:
- This doc does not prescribe authentication variables; consult the Daytona docs linked from https://www.daytona.io/ for current auth guidance.
- Use your app’s feature flags to disable Daytona entirely when not needed.


### 4) Core Operations (to be implemented later)
The Daytona site shows the following Python usage patterns (create sandbox, run code, exec commands, upload files):
```python
from daytona import Daytona

daytona = Daytona()
sandbox = daytona.create()

response = sandbox.process.code_run('print("Hello World!")')
print(response.result)

response = sandbox.process.exec('echo "Hello World from exec!"', cwd="/home/daytona", timeout=10)
print(response.result)

file_content = b"Hello, World!"
sandbox.fs.upload_file("/home/daytona/data.txt", file_content)
```

With parameters (language selection):
```python
from daytona import Daytona, CreateSandboxParams

daytona = Daytona()
params = CreateSandboxParams(language="python")
sandbox = daytona.create(params)
```

Removal (cleanup):
```python
daytona.remove(sandbox)
```

Planned MAMS integration points:
- Evaluation jobs: run scoring scripts or report generators in a sandbox
- Data prep: pre‑process toy datasets for negotiation scenarios
- Tool‑use simulations: controlled execution of small utilities suggested by an agent (kept behind strict policy)


### 5) Execution Model & Policy
- Each sandbox is short‑lived and scoped to a job (negotiation run, batch of evals, etc.)
- Enforce timeouts and output length limits for `code_run` and `exec`
- Deny dangerous operations at the application layer (e.g., disallow arbitrary network egress if your policy requires)
- Limit parallelism via `DAYTONA_MAX_PARALLEL_SANDBOXES`


### 6) File & Artifact Handling
- Upload minimal inputs only (small test datasets, config files)
- Download artifacts on success (e.g., CSV summaries); otherwise just log output
- Use a “sandbox artifacts” folder in your app storage with retention TTL


### 7) Observability
- Emit trace logs for sandbox lifecycle: created_at, started_at, finished_at, status, exit_code, duration_ms
- Log stdout/stderr summaries (redacted) for quick triage
- When Sentry/Galileo are enabled, attach correlation IDs (session_id, negotiation_id, sandbox_id)


### 8) Testing Strategy (after implementation)
- Unit: wrapper that creates/removes a sandbox and runs a no‑op script
- Integration: parallel creation (N sandboxes), ensure bounds respected, verify timeouts
- Failure injection: simulate non‑zero exit, long output, or invalid command; verify clean teardown


### 9) Troubleshooting
- Sandbox fails to start
  - Verify current Daytona status and your account limits
  - Retry with backoff; lower concurrency
- Command timeouts
  - Increase timeout cautiously; profile and optimize code
- File operations fail
  - Verify paths under `/home/daytona/` and byte buffer sizes


### 10) Security Notes
- Treat sandboxes as untrusted; never mount host secrets
- Redact sensitive inputs from logs
- Use short‑lived sandboxes (TTL) and ensure deletion on failure paths


### 11) Rollout Checklist (Docs‑Only)
- [ ] Confirm latest SDK/API usage from Daytona “View Docs” link on https://www.daytona.io/
- [ ] Decide per‑environment flags and parallelism limits
- [ ] Define artifact retention and cleanup policy
- [ ] Add correlation IDs for observability pipelines
- [ ] Link this doc from README and the integration index


