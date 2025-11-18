## Anthropic Claude — Post‑Negotiation Analysis (Docs‑Only)

### 1) Overview
- Goal: Use Anthropic Claude models (via Anthropic's direct API) to perform post‑negotiation analysis and generate concise, decision‑quality summaries.
- Scope: Documentation only. This guide specifies config, request patterns, prompts, testing, and rollout for later implementation.

### 2) Official Documentation (verify before implementing)
- Anthropic API Getting Started: `https://docs.anthropic.com/en/api/getting-started`
- Anthropic Messages API: `https://docs.anthropic.com/en/api/messages`
- Anthropic Python SDK: `https://github.com/anthropics/anthropic-sdk-python`
- Anthropic Console (API Keys): `https://console.anthropic.com/`
- Model Information: `https://docs.anthropic.com/en/docs/models-overview`

### 3) Prerequisites
- Anthropic account and API key from `https://console.anthropic.com/`
- Choose a Claude model (e.g., `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-haiku-20240307`)
- Confirm current model names and availability in Anthropic's documentation before configuring.
- Existing negotiations stored in DB (messages, offers, outcome) to feed the analysis prompt.

### 4) Installation
- Python SDK:
  - `pip install anthropic`
  - Use the Anthropic SDK (`from anthropic import Anthropic`)

### 5) Configuration (Environment)
- Add to backend `.env` (names are suggestions; align with your config schema):
  - `ANTHROPIC_API_KEY=sk-ant-...`  (obtain from https://console.anthropic.com/)
  - `ANTHROPIC_ANALYSIS_MODEL=claude-3-5-sonnet-20241022`  (example only — verify latest model name in Anthropic docs)
  - Optional: `ANTHROPIC_MAX_RETRIES=3` (default retry behavior)
  - Optional: `ANTHROPIC_TIMEOUT=60` (seconds, default varies by SDK)

Document how these map into your app settings (no code yet). If you support per‑session analysis model selection, store it with the session/run.

### 6) Implementation Details (to be implemented later)
- Analysis Service Responsibilities:
  - Inputs: `negotiation_id` → fetch final conversation transcript, offers timeline, constraints, chosen seller (or no‑deal), and any relevant metadata.
  - Build a structured analysis prompt for Claude (see Prompting Notes below).
  - Call Anthropic Messages API with the configured Claude model.
  - Persist the produced analysis summary and key metrics to DB (e.g., reasoning_summary, quality flags).
- Provider Usage:
  - Initialize an Anthropic client with:
    - `api_key=os.environ["ANTHROPIC_API_KEY"]`
    - Optional: `max_retries`, `timeout` from env
  - Provide non‑streaming for post‑run analysis (streaming optional; non‑interactive).
- Error Handling:
  - 401: invalid API key; check key format and permissions.
  - 403: insufficient permissions or account limits.
  - 429: rate limited; SDK handles retries with exponential backoff by default.
  - 5xx: transient errors; SDK retries automatically, cap attempts if needed.

### 7) Usage Examples (reference only; not implemented yet)
- Non‑streaming analysis request (Python):
```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
)

def render_analysis_prompt(context: dict) -> tuple[str, list[dict]]:
    """
    Returns (system_prompt, messages) for Anthropic API.
    context should contain: buyer constraints, seller offers, final outcome,
    rounds, and any notable behavior flags.
    """
    system = (
        "You are an impartial analyst. Summarize the negotiation outcome, "
        "assess decision quality, and highlight trade-offs strictly from the "
        "conversation and constraints—do not invent facts."
    )
    user_content = (
        f"Constraints: {context['constraints']}\n"
        f"Outcome: {context['outcome']}\n"
        f"Offers timeline: {context['offers_timeline']}\n"
        f"Conversation summary: {context['conversation_summary']}\n\n"
        "Produce:\n"
        "1) Brief summary (3-5 sentences)\n"
        "2) Within-budget check and rationale\n"
        "3) Value analysis vs. alternatives\n"
        "4) Suggested improvements for next run"
    )
    messages = [
        {"role": "user", "content": user_content}
    ]
    return system, messages

system_prompt, messages = render_analysis_prompt({
    "constraints": {"item": "USB-C Cable", "qty": 3, "min": 5, "max": 9},
    "outcome": {"type": "deal", "seller": "@QuickTech", "price": 6.75, "qty": 3},
    "offers_timeline": [
        {"seller": "@CableHouse", "price": 8.50},
        {"seller": "@QuickTech", "price": 7.00},
        {"seller": "@BudgetWires", "price": 6.50}
    ],
    "conversation_summary": "Buyer sought sub-$9; compared warranties; chose balanced offer."
})

message = client.messages.create(
    model=os.environ.get("ANTHROPIC_ANALYSIS_MODEL", "claude-3-5-sonnet-20241022"),
    max_tokens=700,
    temperature=0.3,   # More deterministic for analysis
    system=system_prompt,
    messages=messages,
)

analysis_text = message.content[0].text
print(analysis_text)
```

### 8) Prompting Notes (Analysis)
- Keep analysis prompts strictly grounded in the stored transcript, offers, and constraints; avoid speculative or external knowledge.
- Prefer low temperature (e.g., 0.0–0.3) for consistent, reproducible summaries.
- Output format: short, structured sections that the frontend can render directly (e.g., Markdown with headings or bullet points).
- Token Budgeting: keep the conversation summary concise (pre‑summarize with your own logic if needed).

### 9) Testing Strategy (to execute after implementation)
- Unit Tests:
  - Prompt renderer produces expected system prompt and message list given a fixed context.
  - Client wrapper handles non‑streaming responses and extracts text safely.
  - Error mapping: assert behavior on 401/403/429/5xx (mocked).
- Integration Tests:
  - End‑to‑end analysis call in dev with a Claude model via Anthropic API (guarded by env flag).
  - Persisted analysis summary attached to `negotiation_id` and queryable by API.
- Performance:
  - Ensure analysis completes quickly enough for UX (document baseline latency).

### 10) Troubleshooting
- Unauthorized (401):
  - Verify `ANTHROPIC_API_KEY`. Ensure it starts with `sk-ant-` and has no extra whitespace/newlines.
  - Verify key is active in Anthropic Console.
- Forbidden (403):
  - Check account permissions and usage limits in Anthropic Console.
  - Verify billing/credits are available.
- Rate Limits (429):
  - SDK retries automatically with exponential backoff.
  - Reduce request frequency or switch to a smaller/faster Claude model (e.g., claude-3-haiku).
- Large Context:
  - Pre‑summarize the conversation; trim extraneous fields before sending.

### 11) Cost & Usage Considerations
- Pricing is model‑specific; confirm on Anthropic's pricing page: `https://www.anthropic.com/pricing`
- Prefer smaller/faster Claude models (e.g., claude-3-haiku) for routine analyses; reserve larger models (e.g., claude-3-5-sonnet, claude-3-opus) for audits.
- Track token usage to estimate costs once implemented.
- Monitor usage in Anthropic Console.

### 12) Security Best Practices
- Do not log full transcripts or analysis outputs in production unless required; prefer redacted summaries.
- Store API keys in env/secret manager; never commit to source control.
- Use environment variables or secret management systems for API keys.
- Rotate API keys periodically and monitor usage in Anthropic Console.

### 13) Rollout Checklist (Docs‑Only)
- [ ] Choose and document the exact Claude model name from Anthropic docs.
- [ ] Add env variable templates and document defaults.
- [ ] Define the analysis prompt contract and output schema.
- [ ] Document retry/backoff policy (SDK handles automatically).
- [ ] Link this doc from README and the integration index.


