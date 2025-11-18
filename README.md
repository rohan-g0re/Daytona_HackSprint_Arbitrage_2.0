# Arbritrage

Arbritrage simulates realistic, opaque negotiations between one buyer agent and up to ten seller agents per item. Each agent is powered by a local LM Studio model, and all state (configs, chat transcripts, outcomes) is persisted so you can replay or iterate on negotiation strategies without re-entering data. This README distills the working specification from `full_product_idea.md`.

## Core Concept

- **Buyer view**: Knows only the item-level constraints it was configured with (`item`, `quantity`, `min_price`, `max_price`) plus whatever sellers voluntarily disclose in chat. No global budget optimization or handcrafted scoring—buyer reasoning runs purely inside LLM prompts.
- **Seller view**: Each seller is configured with per-item cost, starting ask, and least acceptable price plus style/priorities. Sellers see just the buyer’s messages directed at them and stay stateless between negotiations beyond their stored inventory profile.
- **Opaque interactions**: The buyer cannot see internal seller data; sellers cannot see each other’s responses. An orchestration layer routes messages based on `@handles` while preserving the illusion of separate private conversations.

## Negotiation Loop

1. **Initialization**: Select an item from the configured session. Fetch its buyer constraints and the sellers that stock it.
2. **Conversation**:
   - Buyer opens with a broadcast prompt (e.g., “Need 3 units; what can you offer?”).
   - Orchestrator routes the prompt to all relevant sellers.
   - Sellers respond according to their internal profiles (pricing bounds, tone, retention vs. profit weights).
   - Buyer reviews all visible replies, reasons via LM Studio, follows up, accepts, or walks away—always ensuring the final deal fits the `[min_price, max_price]` band.
3. **Termination**: Store the outcome (deal/no deal, seller, price, quantity, optional reasoning summary) and close the episode.

Multiple negotiation runs can be executed per session to explore different items, prompts, or strategy tweaks while reusing the stored configuration.

## Data Model (Conceptual)

- `Sessions`: top-level configuration bundles.
- `BuyerConfig`: per-item rows with quantity/min/max.
- `SellerConfig`: seller metadata plus behavioral weights/style.
- `SellerInventory`: item-specific pricing constraints.
- `NegotiationRuns`: individual episodes tied to a session + item.
- `Messages`: ordered chat log with routing metadata.
- `Outcomes`: final decision snapshot.

## Runtime & Inference

- All agents call **LM Studio** locally (single-machine, on-device).
- Negotiations run sequentially; “parallel” sellers are simulated by collecting every seller response for a given buyer utterance before letting the buyer think again.
- Responses stream back to the UI for a chat-like experience.

## Repository Layout

```
Hack_NYU/
├─ backend/            # FastAPI application, agents, services, DB layer
├─ frontend/           # Next.js client for configuring sessions & replaying chats
├─ tests/              # Unit, integration, manual scenarios
├─ ENVIRONMENT_SETUP.md
├─ full_product_idea.md
└─ …additional design and provider docs
```

Refer to `ENVIRONMENT_SETUP.md` for platform-specific prerequisites (Windows ARM laptop) and tooling instructions before running any code.

## Getting Started

1. **Environment**: Follow `ENVIRONMENT_SETUP.md` exactly (includes Python env, LM Studio configuration, and provider credentials). Do not substitute tooling—the repo assumes that setup.
2. **Backend**: Launch the FastAPI server (LM Studio must already host the chosen model); it exposes the negotiation orchestration APIs under `backend/app/api/v1`.
3. **Frontend**: Install dependencies with the prescribed Node version, then start the Next.js dev server for the operator UI.
4. **Database**: SQLite file under `backend/data/` stores sessions, runs, and logs. Use the provided scripts/migrations for schema updates.

## Integrations

This project supports multiple cloud-native integrations for enhanced functionality:

- **LLM Providers**: Anthropic Claude (direct API) for agents and post-negotiation analysis
- **Observability**: Galileo AI Observability for LLM evaluation and monitoring
- **Error Tracking**: Sentry for error monitoring and performance tracking
- **Voice**: ElevenLabs for text-to-speech synthesis
- **Development**: Daytona for secure code execution sandboxes
- **Code Quality**: CodeRabbit for automated PR reviews

📚 **See [Integration Documentation Index](docs/INTEGRATION_INDEX.md) for complete setup guides for each integration.**

## Additional References

- `full_product_idea.md`: Canonical narrative spec and behavioral principles.
- `multi-agent-marketplace-architecture.md`: Sequence diagrams and orchestration details.
- `FORCE_DECISION_IMPLEMENTATION.md`: How forced decisions are handled inside the buyer agent.
- `MESSAGING_BUGS_FIX_SUMMARY.md`, `PROVIDER_IMPLEMENTATION_SUMMARY.md`, etc.: Phase-by-phase change logs.

For questions or contributions, open an issue referencing the relevant spec section so reviewers can cross-check with `full_product_idea.md`.

