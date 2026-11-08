# Performance and resource envelope

- Captured input: 20,000 characters maximum.
- Aggregated provider output: 20,000 characters maximum.
- Passive-monitor debounce: 750 ms; duplicate clipboard digests are skipped.
- One provider worker at a time. A new request is refused while the previous worker is still stopping.
- Cancellation is cooperative between streamed chunks; a blocked provider SDK call may delay shutdown.
- Keys, prompts, responses, and conversation state remain process-memory only.

Latency and memory depend on the selected Ollama model or cloud provider. CI validates deterministic policies with fake providers and offscreen Qt; release review should exercise explicit capture, monitoring consent, cancellation, tray exit, keyboard navigation, and each configured provider on a clean Windows source checkout.
