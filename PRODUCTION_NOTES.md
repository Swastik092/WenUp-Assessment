# Production Notes

The current Day 2 implementation fulfills the assessment brief, but requires several infrastructural and architectural upgrades before it can be deployed to a true production environment.

## 1. Persistent Storage
- **Current State**: Sessions are stored in a volatile, in-memory `dict` within `conversation_service.py`. Data is lost on server restart.
- **Production Path**: Migrate session state to a persistent datastore (e.g., PostgreSQL for relational structured data, or Redis for fast, ephemeral session caches).

## 2. Authentication & Session Security
- **Current State**: Sessions are purely ID-based with no user authentication. Anyone with a session ID can access and modify that state.
- **Production Path**: Integrate robust authentication (OAuth 2.0 / JWTs). Bind sessions explicitly to authenticated user IDs to prevent horizontal privilege escalation.

## 3. Rate-Limiting the LLM Endpoint
- **Current State**: The `/api/chat` endpoint can be spammed, leading to uncontrolled Gemini API consumption and cost spikes.
- **Production Path**: Implement API Gateway or middleware rate-limiting (e.g., using Redis bucket algorithms) specifically around the expensive LLM extraction routes to prevent abuse.

## 4. Structured Logging & Observability
- **Current State**: Basic Python `logging.info` and standard exception printing.
- **Production Path**: Use structured JSON logging (e.g., structlog) combined with OpenTelemetry to trace user requests through the orchestrator to the LLM. Monitor LLM token usage and latency.

## 5. Resilience (Exponential Backoff & Circuit Breaking)
- **Current State**: A naive `for attempt in range(2)` retry loop that immediately retries upon failure.
- **Production Path**: Implement exponential backoff (e.g., `tenacity` library) to respect 429 Rate Limits from the LLM provider. Implement circuit breakers to fail-fast if the LLM provider experiences a sustained outage, falling back gracefully immediately.

## 6. Streaming Responses
- **Current State**: The frontend blocks and waits while the backend calls the LLM, validates, generates the document, and replies.
- **Production Path**: Transition the LLM generation and API routes to support Server-Sent Events (SSE). Stream the assistant's reply tokens back to the frontend in real-time to drastically reduce perceived latency.

## 7. Prompt-Injection Hardening
- **Current State**: The user's free-text message is interpolated directly into the Gemini prompt via an f-string in `_build_prompt`.
- **Production Path**: 
  - Utilize proper system message demarcation and potentially intermediate LLM sanitization layers.
  - While we limit damage because the state manager strictly validates outputs, a malicious user could still attempt to jailbreak the model into emitting invalid JSON or looping. A pre-flight intent classification or strict input length bounds should be enforced.
