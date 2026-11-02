# Architecture

Sparkle AI is being separated incrementally so that safety behavior can be reviewed without a GUI
rewrite.

```text
Explicit hotkey or tray action
          |
          v
Packaged PyQt interface (`sparkle_ai.desktop`)
          |
          v
InputPolicy -> AnalysisService -> TextProvider
                                   |
                                   +-- OllamaProvider (default, loopback)
                                   `-- GeminiProvider (optional, not wired to UI)
```

## Trust boundaries

- Clipboard text is untrusted and may contain sensitive data or adversarial instructions.
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
the bridge, extracted core, and fake-provider behavior. CI builds and smoke-tests the installed
launcher on Windows, while clean-VM GUI, hotkey, Ollama, signing, and installer tests remain release
gates.
