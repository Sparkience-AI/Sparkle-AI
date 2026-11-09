# Sparkle AI

Sparkle AI is an experimental, privacy-first Windows desktop assistant for analyzing clipboard
text through local Ollama or an explicitly selected Gemini, OpenAI, or Anthropic BYOK session. It supports the
original background clipboard workflow as a visibly enabled, session-only opt-in while retaining
explicit hotkey and tray capture.

> **Maturity:** pre-alpha source-run developer preview.

## Current product boundary

Sparkle AI currently supports:

- User-invoked clipboard analysis with `Ctrl+Shift+Space` or the tray menu.
- Optional automatic clipboard monitoring with visible tray state, debounce, deduplication, and
  automatic rejection of likely credentials or oversized/binary content.
- Loopback-only Ollama access at `127.0.0.1:11434`.
- Runtime provider and model choice between local Ollama, Google Gemini, OpenAI, and Anthropic
  Claude. Cloud routes require an in-memory user API key and explicit transmission consent.
- A bounded 20,000-character text payload.
- Streaming output with cooperative cancellation between provider chunks.
- Unified cancellation for close-button, outside-click, disable, and fresh-capture paths.
- Response and follow-up context reset when a provider, model, or cloud key changes.
- A testable application core independent of the PyQt interface.

Sparkle AI does **not** persist conversation history or credentials, install a background service,
provide automatic updates, or offer a supported public/cloud-hosted version.

## Requirements

- Windows 11 for the current developer-preview target. Windows 10 support remains an owner
  decision and has not been verified.
- Python 3.11, 3.12, or 3.13.
- [uv](https://docs.astral.sh/uv/).
- A local [Ollama](https://ollama.com/) daemon and the `llama3.2:3b` model.

## Local setup

```powershell
git clone https://github.com/Sparkience-AI/Sparkle-AI.git
cd Sparkle-AI
uv sync --locked
ollama pull llama3.2:3b
uv run --locked sparkle-ai
```

Copy text, then press `Ctrl+Shift+Space`. The text is read only after that explicit action. Pause
capture through the tray toggle and exit through the tray menu. To restore the original automatic
workflow, enable **Monitor clipboard automatically** in the tray and accept the session notice.

Cloud providers are optional. Install only the provider integrations you need:

```powershell
uv sync --locked --extra gemini
uv sync --locked --extra openai
uv sync --locked --extra anthropic
```

Choose a BYOK entry under **Provider**, enter a key and model identifier, and approve cloud
transmission. Keys are kept only in process memory and can be cleared individually from the menu.

## Privacy and provider behavior

The default route is the local Ollama loopback service. Captured text is not written to files or
default logs by Sparkle AI. Model behavior can still be incorrect, and text copied from other
applications may contain secrets or malicious instructions. Review the exact clipboard contents
before invoking analysis.

Each cloud route requires its matching extra and passes the key directly to a session-owned client.
The tray and overlay always show the active provider. Enabling automatic monitoring with any cloud
provider requires a separate warning because each accepted clipboard change leaves the machine.
OpenAI requests explicitly disable response storage at the request boundary. See
[Privacy](docs/privacy.md).

## Architecture

The packaged PyQt interface and testable logic live under `src/sparkle_ai`; the root `main.py`
remains a source-checkout compatibility launcher:

- `capture.py`: opt-in monitoring, deduplication, secret heuristics, and in-memory provider state.
- `desktop.py`: GUI-thread bridge, tray/hotkey/monitor integration, overlay, and worker lifecycle.
- `application.py`: input policy, cancellation boundary, and streaming orchestration.
- `providers.py`: loopback Ollama plus optional Gemini, OpenAI Responses, and Anthropic Messages adapters.
- `prompts.py`: versioned, injection-aware prompt construction.

See [Architecture](docs/architecture.md), [Threat model](docs/threat-model.md), and
[Release checklist](docs/release-checklist.md).

Operational boundaries are documented in the [performance envelope](docs/performance.md) and
[accessibility contract](docs/accessibility.md).

## Development

```powershell
uv sync --locked
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pytest
uv build --no-sources
```

Normal tests use fake providers and do not require Ollama, cloud API keys, or network
access. CI also builds and smoke-tests the source-installed Windows launcher on Python 3.11–3.13.

## Security and support

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md). This developer
preview has no persistent background service, telemetry, or hosted demo.

## License notice

The repository currently contains a GPL-2.0 license while PyQt6 has separate licensing terms.
Contributors must review compatibility before changing dependencies or redistribution terms;
Sparkle AI is distributed and verified here as source-run software only.
