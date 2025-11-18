## ElevenLabs Voice (Text-to-Speech) — Integration Documentation (Docs‑Only)

This guide documents how to add ElevenLabs Text‑to‑Speech to MAMS so seller responses can be rendered as audio, with per‑seller voices and optional streaming. It outlines configuration, request patterns, streaming, caching, and rollout for later implementation.

### Official documentation (verify before implementing)
- ElevenLabs site (Docs entry available from navbar): `https://elevenlabs.io/`
- API reference (TTS): `https://elevenlabs.io/docs/api-reference/`
- Python SDK (reference): `https://github.com/elevenlabs/elevenlabs-python`
- JavaScript SDK (reference): `https://github.com/elevenlabs/elevenlabs-js`


### 1) What We Want
- Convert seller agent text responses to speech with consistent, assigned voices
- Support both on‑demand generation and pre‑generation with caching
- Optional streaming playback to the browser for chat‑like UX
- Low overhead and configurable audio formats (mp3/pcm/ogg)


### 2) Prerequisites
- ElevenLabs account and API key
- Choose a default TTS model (e.g., `eleven_multilingual_v2`) — confirm current model names/pricing in the official docs
- Select or create voice IDs for sellers (from the ElevenLabs dashboard or via API)


### 3) Configuration (Environment templates)
Add placeholders to `.env` (align with your config loader):
```
ELEVENLABS_ENABLED=true
ELEVENLABS_API_KEY=
ELEVENLABS_TTS_MODEL=eleven_multilingual_v2
ELEVENLABS_OUTPUT_FORMAT=mp3_44100_128    # alternatives: mp3_22050_32, pcm_16000, ogg_44100_64, etc.

# Optional per‑seller mapping (document approach; persist in DB or config)
ELEVENLABS_DEFAULT_VOICE_ID=
# Example mapping (store in DB/config, not env):
#   {"@TechMart":"JBFqnCBsd6RMkjVDRZzb", "@BudgetBytes":"ABCD1234...", "@ProGear":"EFGH5678..."}
```


### 4) Integration Approach (to implement later)
Backend Voice Service responsibilities:
- Inputs: `seller_handle`, `text`, optional overrides (`voice_id`, `model`, `format`)
- Output: audio bytes (non‑stream) or an async generator (stream)
- Caching: key on `(seller_handle, text_hash, model, format)`; store short‑lived artifacts under `/data/tts-cache`
- Rate limiting/backoff on HTTP 429; transient retry on 5xx
- Privacy: never send sensitive metadata as “text” (TTS), only the textual message

Non‑streamed flow:
1. Receive seller text response
2. Lookup `voice_id` for seller (fallback to default)
3. Check cache → hit: return cached audio; miss: request TTS, store, return
4. Expose a signed URL (short TTL) or direct binary response for the audio

Streamed flow:
1. Initiate TTS request with streaming output (PCM or chunked MP3 where supported)
2. Pipe chunks to client via SSE/WebSocket/media endpoint
3. Optionally also persist a final MP3 for later replay


### 5) Usage Examples (reference only; not implemented yet)
Python (SDK) — simple non‑stream:
```python
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

audio = client.text_to_speech.convert(
    text="Thanks for your interest. I can offer $6.75 each with a 1-year warranty.",
    voice_id="JBFqnCBsd6RMkjVDRZzb",              # map from seller handle
    model_id=os.environ.get("ELEVENLABS_TTS_MODEL", "eleven_multilingual_v2"),
    output_format=os.environ.get("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128"),
)

# Return as binary from FastAPI or save to cache file then serve via URL
```

Node.js (SDK) — simple non‑stream:
```javascript
import { ElevenLabsClient } from '@elevenlabs/elevenlabs-js';

const client = new ElevenLabsClient({ apiKey: process.env.ELEVENLABS_API_KEY });

const audio = await client.textToSpeech.convert('JBFqnCBsd6RMkjVDRZzb', {
  text: "Hello! We can match $6.75 and ship today.",
  modelId: process.env.ELEVENLABS_TTS_MODEL || 'eleven_multilingual_v2',
  // format defaults vary by SDK; set explicitly if needed
});

// Send audio buffer to the browser or persist to storage
```

Streaming notes:
- Prefer PCM (`pcm_16000`) for low‑latency WebAudio playback, or chunked MP3 for compatibility
- In the browser, use MediaSource Extensions or WebAudio for smooth playback
- On the server, use an async generator/StreamingResponse to forward chunks


### 6) Frontend Integration (planned)
- Chat UI: when a seller response arrives, request `/audio/{message_id}` or receive a pre‑attached audio URL
- Provide a minimal audio player (play/pause, seek if non‑streamed)
- Handle loading, fallback to text if audio not available/failed
- Optional: “Voice per seller” legend or selector in config UI


### 7) Caching & Storage
- File naming: `<negotiation_id>_<round>_<seller_handle>_<hash>.mp3`
- TTL: configurable (e.g., 24–72 hours) with background cleanup
- Consider S3/Blob storage for persistence in production; local disk in dev


### 8) Testing Strategy (after implementation)
- Unit tests: voice mapping, cache keying, format selection, retry logic
- Integration: generate audio for several sellers in one round; verify URLs and playback
- Performance: measure TTS latency; abort TTS on client cancel; ensure non‑blocking
- Failover: when TTS is disabled or quota exceeded, UI still shows text gracefully


### 9) Troubleshooting
- 401/403 Unauthorized:
  - Verify `ELEVENLABS_API_KEY` and account permissions
- 404 Voice not found:
  - Confirm `voice_id` exists and you have access; re‑sync mapping
- 415 / unsupported format:
  - Pick a supported `output_format` per the API reference
- 429 Rate limit:
  - Implement backoff; cache more aggressively; pre‑generate common phrases
- Audio pops/gaps (streaming):
  - Prefer PCM for lowest latency; ensure client buffer is adequate


### 10) Cost & Usage Considerations
- TTS is billed per character or time; confirm pricing in your ElevenLabs plan
- Reduce costs by caching commonly repeated system phrases or summaries
- Avoid generating audio for long messages when not needed (UI user setting)


### 11) Security & Privacy
- Never log API keys or full audio payloads
- Redact sensitive data from text before TTS if policy requires
- Serve audio via signed URLs with short TTL when stored


### 12) Rollout Checklist (Docs‑Only)
- [ ] Confirm model and supported `output_format` in official docs
- [ ] Establish seller‑to‑voice mapping policy and storage
- [ ] Implement cache and cleanup policy
- [ ] Define streaming vs non‑streamed behavior per environment
- [ ] Link this doc from README and the integration index


