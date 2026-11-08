# Threat model

Protected assets are clipboard text, provider credentials, model output, and control of the local desktop session. Sparkle AI is not a sandbox and model output is never trusted as instructions.

Primary threats include accidental clipboard disclosure, passive-monitoring surprise, copied credentials, prompt injection, cloud-provider misrouting, API-key leakage, remotely exposed Ollama, oversized input/output, stuck provider streams, global-hotkey abuse, and dependency compromise.

Controls include explicit capture by default, visible session-only monitoring opt-in, debounce/deduplication, credential heuristics, 20,000-character input and output limits, loopback-only Ollama, session-memory BYOK keys, provider-specific consent/clear actions, OpenAI storage disabled, sanitized errors, GUI-thread signal bridging, cooperative cancellation, accessible provider/status labels, and pinned CI actions.

Residual risks include false negatives in secret detection, other local processes reading the clipboard or memory, providers retaining data under their own account policy, blocking SDK calls that cannot stop until the next chunk, and vulnerabilities in Qt, keyboard hooks, models, or dependencies. Use explicit capture for sensitive work and verify the provider before every cloud transmission.
