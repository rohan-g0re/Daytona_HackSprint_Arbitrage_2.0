## Integration Documentation Index

Quick navigation for all integration guides used by MAMS. Each page includes env configuration, implementation notes (docs‑only), testing strategy, troubleshooting, costs, and security.

### Core LLM & Analysis
- Anthropic Claude (Direct API): `./ANTHROPIC_CLAUDE.md`
  - References: `https://docs.anthropic.com/en/api/getting-started`, `https://docs.anthropic.com/en/api/messages`, `https://console.anthropic.com/`
- Anthropic Claude (Post‑Negotiation Analysis): `./GEMINI_ANALYSIS.md`
  - References: `https://docs.anthropic.com/en/api/getting-started`, `https://docs.anthropic.com/en/api/messages`, `https://console.anthropic.com/`

### Observability & Quality
- Galileo AI Observability: `./GALILEO_INTEGRATION.md`
  - References: `https://galileo.ai/` (Docs via site navbar)
- Sentry Error Monitoring & Performance: `./SENTRY_INTEGRATION.md`
  - References: `https://docs.sentry.io/platforms/`, `https://docs.sentry.io/platforms/python/guides/fastapi/`, `https://docs.sentry.io/platforms/javascript/guides/nextjs/`

### Voice
- ElevenLabs Text‑to‑Speech: `./ELEVENLABS_VOICE.md`
  - References: `https://elevenlabs.io/`, `https://elevenlabs.io/docs/api-reference/`

### Dev Environments & Code Reviews
- Daytona Setup (Sandboxes): `./DAYTONA_SETUP.md`
  - References: `https://www.daytona.io/` (View Docs)
- CodeRabbit AI Code Review: `./CODERABBIT_SETUP.md`
  - References: `https://www.coderabbit.ai/`, `https://docs.coderabbit.ai/`

### Usage Order (recommended)
1) Configure providers (Claude for agents and analysis) → 2) Enable observability (Galileo/Sentry) → 3) Add voice (ElevenLabs) → 4) Wire Daytona for code execution use‑cases → 5) Turn on CodeRabbit for PR reviews.


