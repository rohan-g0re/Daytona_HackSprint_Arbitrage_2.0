## Galileo AI Observability — Integration Documentation (Docs-Only)

This guide documents how to instrument the Multi‑Agent Marketplace Simulator (MAMS) for AI observability and evaluation using Galileo. It specifies configuration, data to capture, and testing/rollout plans for later implementation.

References (official entry point):
- Galileo site (Docs entry available from navbar): [https://galileo.ai/](https://galileo.ai/)

Note: Always confirm current SDKs, ingestion options, and evaluator capabilities from the official Docs link on the Galileo site before implementing.


### 1) What We Want
- End‑to‑end visibility into agent behavior across Buyer/Seller reasoning turns
- Quality/evaluation signals (hallucination risk, safety, coherence) for each LLM call
- Real‑time production monitoring (sampling configurable) with privacy safeguards
- Minimal overhead and vendor‑agnostic provider routing (LM Studio/OpenRouter)


### 2) What To Capture (Trace Schema – planned)
Capture one “trace” per LLM call (and aggregate per negotiation run), including:
- request_id, correlation_id, session_id, negotiation_id, round_number
- provider, model, temperature, max_tokens, stop, latency_ms, status_code
- prompt_role segments (system, user, assistant) with redaction applied
- output_text (sanitized), token_counts (prompt/output/total) where available
- quality flags (e.g., “within_budget_check”, “price_floor_respected” – computed app‑side)
- error fields (type, message) for failure cases
- PII/sensitive flags (boolean) after app‑side scrubbing

Sampling:
- Dev: 100%
- Staging: 10–30%
- Prod: 1–10% (raise to 100% during incidents)

Data retention:
- Align with company policy; document retention duration and deletion workflow.


### 3) Privacy & Redaction Policy
Before sending to Galileo:
- Remove or hash direct identifiers (names, emails, order IDs) unless explicitly needed
- Drop secrets/tokens entirely (never log keys)
- Optional: replace prices with buckets (e.g., “$6–$7”) if required by policy
- Maintain a “redaction map” in memory only (not persisted)


### 4) Configuration (Environment – templates only)
Add placeholders to `.env` (final names may change after reviewing official docs):
```
# Toggle
GALILEO_ENABLED=true
GALILEO_ENV=development  # development|staging|production

# Auth (obtain from Galileo; never commit secrets)
GALILEO_API_KEY=

# Endpoint/ingestion options (confirm from official docs)
GALILEO_INGEST_URL=
GALILEO_TIMEOUT_MS=5000

# Sampling
GALILEO_SAMPLE_RATE=1.0  # 0.0–1.0

# Privacy
GALILEO_REDACT_SENSITIVE=true
```


### 5) Instrumentation Plan (to implement later)
Where to instrument:
- LLM provider wrapper (`backend/app/llm/*`): wrap `generate` and `stream` to emit traces
- Negotiation graph events (`backend/app/agents/graph_builder.py`): send round‑level summary
- API endpoints (`backend/app/api/v1/endpoints/*`): emit high‑level request spans
- Error middleware: capture exceptions with correlation_id

Batching & resilience:
- Queue traces in memory; flush on interval or batch size threshold
- Non‑blocking network calls with timeouts; drop on backpressure
- Circuit breaker: auto‑disable Galileo if repeated failures exceed threshold

PII‑safe logging helpers:
- `redact_text(text) -> text`: remove emails, phone numbers, IDs
- `sanitize_messages(messages) -> messages`: apply role‑aware redaction


### 6) Evaluations & Metrics (planned)
Use Galileo’s evaluation surface (per official docs) to track, at minimum:
- Hallucination risk indicators
- Safety/guardrail metrics (prompt injection, PII leakage patterns)
- Coherence/consistency signals across rounds
- Agent‑specific metrics (decision latency, number of counter‑offers, adherence to price bounds)

App‑side computed metrics to include with traces:
- `offer_within_buyer_band` (bool)
- `seller_floor_violated` (bool)
- `rounds_to_decision` (int)
- `decision_type` (deal|no_deal)

Front‑of‑house dashboards (once implemented):
- Per‑session: success rate, avg price vs ask, avg rounds, latency, eval scores
- Per‑model: quality vs cost (tokens, response time), error rate
- Alerts: sudden drop in coherence/safety, spike in timeouts or 5xx


### 7) Pseudocode (reference only; not actual code)
```python
def with_galileo_trace(fn):
    def wrapper(*args, **kwargs):
        if not settings.GALILEO_ENABLED or random() > settings.GALILEO_SAMPLE_RATE:
            return fn(*args, **kwargs)
        trace = start_trace()
        try:
            start = monotonic()
            result = fn(*args, **kwargs)
            latency_ms = int((monotonic() - start) * 1000)

            payload = {
                "request_id": trace.id,
                "provider": context.provider,
                "model": context.model,
                "latency_ms": latency_ms,
                "messages": sanitize_messages(context.messages),
                "output_text": redact_text(result.text),
                "token_counts": result.usage or {},
                "quality_flags": compute_quality_flags(context, result),
                "status_code": 200,
            }
            enqueue_to_galileo(payload)
            return result
        except Exception as e:
            enqueue_to_galileo({
                "request_id": trace.id,
                "error": {"type": type(e).__name__, "message": str(e)[:200]},
                "status_code": 500,
            })
            raise
    return wrapper
```


### 8) Testing Strategy (after implementation)
- Unit tests: redaction functions, sampling logic, enqueue/backoff behavior
- Integration tests: run a short negotiation; assert traces batched and sent
- Load tests (dev): ensure overhead < 5–10% at target RPS
- Privacy checks: verify no secrets/PII leak into payloads


### 9) Troubleshooting
- No data in dashboard:
  - Check `GALILEO_ENABLED`, API key, ingest URL, and network egress
  - Verify sampling rate and that traces are not filtered out
- High latency:
  - Increase batch size, reduce flush frequency, or lower sample rate
  - Ensure async I/O and timeouts are configured
- Payload rejected:
  - Validate shape/fields against official schema (see Docs from [galileo.ai](https://galileo.ai/))


### 10) Cost & Usage Considerations
- Control ingestion volume via `GALILEO_SAMPLE_RATE`
- Prefer redacted, compact payloads; cap transcript length
- Align retention and export with compliance requirements


### 11) Security Best Practices
- Store API keys in env/secret manager; never commit
- Redact sensitive text before enqueueing
- Limit who can query raw traces; prefer summarized views in UI


### 12) Rollout Checklist (Docs‑Only)
- [ ] Confirm authentication method and ingest endpoint from official Docs
- [ ] Finalize trace schema and redaction rules
- [ ] Define sampling and retention policies per environment
- [ ] Document alert thresholds and on‑call runbooks
- [ ] Link this doc from README and the integration index


