# Architecture

Sparkle AI is being separated incrementally so that safety behavior can be reviewed without a GUI
rewrite.

```text
Explicit hotkey or tray action
          |
          v
PyQt interface (`main.py`)
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
- Ollama is constrained to the loopback default. Publicly exposing an Ollama daemon is outside the
  supported contract.

## Current extraction boundary

The UI, tray integration, global hotkey, and worker thread remain in `main.py`. Moving them before
the PyQt/PySide licensing decision would create unnecessary churn. Unit tests target the extracted
core and fake-provider behavior. Windows UI and clean-machine package tests remain release gates.
