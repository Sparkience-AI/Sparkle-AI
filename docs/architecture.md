# Architecture

Sparkle AI is being separated incrementally so that safety behavior can be reviewed without a GUI
rewrite.

```text
Explicit capture or opt-in monitored clipboard change
          |
          v
Packaged PyQt interface (`sparkle_ai.desktop`)
          |
          v
InputPolicy -> AnalysisService -> TextProvider
                                   |
                                   +-- OllamaProvider (default, loopback)
                                   `-- GeminiProvider (opt-in, in-memory BYOK)
```

## Trust boundaries

- Clipboard text is untrusted and may contain sensitive data or adversarial instructions.
- `ClipboardMonitorState` owns opt-in, deduplication, size/null checks, and credential heuristics;
  the GUI-owned timer provides debounce.
- The PyQt interface may request work but does not construct provider prompts.
- The application service validates input, owns cancellation state, and streams only text chunks.
- Provider adapters receive application-owned prompts and must not mutate process-global credential
  state.
- Ollama endpoints are validated as explicit loopback URLs. Publicly exposing an Ollama daemon is outside the
  supported contract.

## Current extraction boundary

The UI, tray integration, global hotkey, and worker thread remain together in `desktop.py`; this is
a packaging move, not a PyQt/PySide rewrite. A Qt signal bridge marshals the global-hotkey callback
onto the GUI thread, while a cancellable Qt timer owns deferred request starts. Unit tests target
the bridge, monitoring/provider state, extracted core, overlay follow-up signal, and fake-provider
behavior. CI installs all optional providers, then builds and smoke-tests the installed launcher on
Windows, while clean-VM GUI, hotkey, live-provider, signing, and installer tests remain release gates.
