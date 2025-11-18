## Anthropic Claude — Direct API Implementation Documentation (Docs-Only)

### 1) Overview
- Goal: Route Buyer/Seller agent reasoning through Anthropic Claude models using Anthropic's direct API.
- Scope: Documentation only. This guide specifies configuration, interfaces, and testing strategy to implement later.

### 2) Official Documentation (verify before implementing)
- Anthropic API Getting Started: `https://docs.anthropic.com/en/api/getting-started`
- Anthropic Messages API: `https://docs.anthropic.com/en/api/messages`
- Anthropic Python SDK: `https://github.com/anthropics/anthropic-sdk-python`
- Anthropic Console (API Keys): `https://console.anthropic.com/`
- Model Information: `https://docs.anthropic.com/en/docs/models-overview`

### 3) Prerequisites
- Anthropic account and API key from `https://console.anthropic.com/`
- Choose a Claude model (e.g., `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-haiku-20240307`)
- Confirm current model names and availability in Anthropic's documentation before rollout.

### 4) Installation
- Python SDK:
  - `pip install anthropic`
  - Use the Anthropic SDK (`from anthropic import Anthropic`)

### 5) Configuration (Environment)
- Add to backend `.env` (documented names; adjust if your project uses different keys):
  - `LLM_PROVIDER=anthropic`
  - `ANTHROPIC_API_KEY=sk-ant-...`  (obtain from https://console.anthropic.com/)
  - `ANTHROPIC_DEFAULT_MODEL=claude-3-5-sonnet-20241022`  (example; confirm latest model name in Anthropic docs)
  - Optional: `ANTHROPIC_API_VERSION=2023-06-01` (default is usually latest)
  - Optional: `ANTHROPIC_MAX_RETRIES=3` (default retry behavior)
  - Optional: `ANTHROPIC_TIMEOUT=60` (seconds, default varies by SDK)

Document the mapping in your config file (no code yet). For per-session provider selection, store the chosen provider/model with the Session record.

### 6) Implementation Details (to be implemented later)
- Provider Factory:
  - Instantiate the Anthropic client with:
    - `api_key=os.environ["ANTHROPIC_API_KEY"]`
    - Optional: `max_retries`, `timeout` from env
  - Expose `generate(messages, temperature, max_tokens, stop, model)` and `stream(...)`.
- Model Naming:
  - Use Anthropic model names exactly as documented, e.g., `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`, `claude-3-haiku-20240307` (verify latest names in Anthropic docs).
- Request Shape (Messages API):
  - Messages array of `{ "role": "user"|"assistant", "content": "..." }`.
  - System prompt passed separately via `system` parameter (not in messages array).
  - Parameters: `temperature`, `max_tokens`, optional `stop_sequences`.
- Streaming:
  - Use `stream=True`. Parse Server-Sent Events (SSE) format with `text_delta` events from the stream.
- Error Handling:
  - 401 → invalid API key; check key format and permissions.
  - 403 → insufficient permissions or account limits.
  - 429 → rate limit; SDK handles retries with exponential backoff by default.
  - 5xx → transient provider error; SDK retries automatically, cap attempts if needed.

### 7) Usage Examples (reference only; not implemented yet)
- Non-streaming (Python):
```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
)

message = client.messages.create(
    model=os.environ.get("ANTHROPIC_DEFAULT_MODEL", "claude-3-5-sonnet-20241022"),
    max_tokens=500,
    temperature=0.7,
    system="You are a strategic buyer negotiating within constraints.",
    messages=[
        {"role": "user", "content": "I need 3 USB-C cables under $9 each. What can you offer?"}
    ],
)

text = message.content[0].text
print(text)
```

- Streaming (Python):
```python
import os
from anthropic import Anthropic

client = Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"],
)

with client.messages.stream(
    model="claude-3-5-sonnet-20241022",
    max_tokens=200,
    temperature=0.7,
    messages=[{"role": "user", "content": "Stream a short reply."}],
) as stream:
    for text_block in stream.text_stream:
        # text_block is a string chunk
        print(text_block, end="", flush=True)
print()
```

### 8) Prompting Notes (Buyer/Seller)
- Buyer:
  - System prompt includes: item, quantity, min/max price; objective to pick best offer based on conversation evidence only (no scoring formulas).
- Seller:
  - System prompt includes: cost (never reveal), selling price, least price, style, and priorities. Enforce never going below least price.
- Prompt Templates:
  - Keep role separation clear; avoid leaking hidden seller data to buyer prompts.
  - Keep messages concise to conserve tokens (document your token budgeting policy).

### 9) Testing Strategy (to execute after implementation)
- Unit Tests:
  - Factory returns Anthropic provider when configured.
  - Non-stream and stream result parsing with mocked responses.
  - Error mapping for 401/403/429/5xx.
- Integration Tests:
  - Health/status endpoint includes current provider and model.
  - Simple round-trip request to Anthropic API with a Claude model in a dev environment (guarded by env flag).
- Performance:
  - Verify reasonable latency per call (document baseline).
  - SDK handles retries automatically; verify backoff behavior.

### 10) Troubleshooting
- 401 Unauthorized:
  - Check `ANTHROPIC_API_KEY`. Ensure it starts with `sk-ant-` and has no extra whitespace/newlines.
  - Verify key is active in Anthropic Console.
- 403 Forbidden:
  - Check account permissions and usage limits in Anthropic Console.
  - Verify billing/credits are available.
- 429 Rate Limit:
  - SDK retries automatically with exponential backoff.
  - Reduce concurrency or token usage if limits persist.
  - Consider using a smaller/faster model (e.g., claude-3-haiku) for development.
- TLS/Network Issues:
  - Confirm outbound HTTPS to `api.anthropic.com`.
  - Check proxies/enterprise firewalls.

### 11) Cost & Usage Considerations
- Pricing is model-specific; confirm on Anthropic's pricing page: `https://www.anthropic.com/pricing`
- Use smaller/faster models (claude-3-haiku) in development; switch to higher-quality models (claude-3-5-sonnet, claude-3-opus) for evaluation runs.
- Log prompt/response token counts to estimate costs (once implemented).
- Monitor usage in Anthropic Console.

### 12) Security Best Practices
- Never commit API keys. Load from environment or secure vault.
- Limit logs to non-sensitive metadata; avoid logging full prompts/responses in production.
- Use environment variables or secret management systems for API keys.
- Rotate API keys periodically and monitor usage in Anthropic Console.

### 13) Rollout Checklist (Docs-Only)
- [ ] Verify chosen model name in Anthropic docs and note it in `.env` templates.
- [ ] Document environment variables and default values.
- [ ] Document provider selection rules (global vs per-session).
- [ ] Document retry/backoff policy (SDK handles automatically).
- [ ] Add links to this doc from the main README and integration index.


