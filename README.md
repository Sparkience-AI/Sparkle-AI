# Sparkle AI

Sparkle AI is an experimental, privacy-first Windows desktop assistant for analyzing clipboard
text through a local Ollama model or an explicitly selected Gemini BYOK session. It supports the
original background clipboard workflow as a visibly enabled, session-only opt-in while retaining
explicit hotkey and tray capture.

> **Maturity:** pre-alpha developer preview. There is no supported binary installer yet. Do not
> distribute a bundled application until the PyQt and project-license decision is resolved.

## Current product boundary

Sparkle AI currently supports:

- User-invoked clipboard analysis with `Ctrl+Shift+Space` or the tray menu.
- Optional automatic clipboard monitoring with visible tray state, debounce, deduplication, and
  automatic rejection of likely credentials or oversized/binary content.
- Loopback-only Ollama access at `127.0.0.1:11434`.
- Runtime provider choice between local Ollama and Google Gemini 3.8 Flash. Gemini requires an
  in-memory user API key and explicit cloud-transmission consent.
- A bounded 20,000-character text payload.
- Streaming output with cooperative cancellation between provider chunks.
- A testable application core independent of the PyQt interface.

Sparkle AI does **not** persist conversation history or credentials, install a background service,
provide an installer or automatic updates, or offer a supported public/cloud-hosted version.

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

Gemini is optional:

```powershell
uv sync --locked --extra gemini
```

Choose **Provider → Google Gemini (BYOK)**, enter a key, and approve cloud transmission. The key is
kept only in process memory and can be cleared from the Provider menu.

## Privacy and provider behavior

The default route is the local Ollama loopback service. Captured text is not written to files or
default logs by Sparkle AI. Model behavior can still be incorrect, and text copied from other
applications may contain secrets or malicious instructions. Review the exact clipboard contents
before invoking analysis.

The Gemini route requires the `gemini` extra and a key passed directly to a session-owned client.
The tray and overlay always show the active provider. Enabling automatic monitoring while Gemini
is selected requires a separate warning because each accepted clipboard change is sent to Google.
See [Privacy](docs/privacy.md).

## Architecture

The packaged PyQt interface and testable logic live under `src/sparkle_ai`; the root `main.py`
remains a source-checkout compatibility launcher:

- `capture.py`: opt-in monitoring, deduplication, secret heuristics, and in-memory provider state.
- `desktop.py`: GUI-thread bridge, tray/hotkey/monitor integration, overlay, and worker lifecycle.
- `application.py`: input policy, cancellation boundary, and streaming orchestration.
- `providers.py`: loopback Ollama and optional Gemini adapters.
- `prompts.py`: versioned, injection-aware prompt construction.

See [Architecture](docs/architecture.md) and [Open decisions](docs/decisions-needed.md).

## Development

```powershell
uv sync --locked
uv run --locked ruff format --check .
uv run --locked ruff check .
uv run --locked pytest
uv build --no-sources
```

Normal tests use fake providers and do not require Ollama, Gemini, a Google API key, or network
access. CI also builds and smoke-tests the installed Windows launcher on Python 3.11–3.13. This is
package verification, not a signed installer or full GUI acceptance test.

## Security and support

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md). This developer
preview has no persistent background service, telemetry, hosted demo, or binary release channel.

## License notice

The repository currently contains a GPL-2.0 license while PyQt6 is distributed under GPLv3 or a
commercial license. This combination requires a documented licensing review. The project is not
claiming that its current metadata is ready for binary redistribution.
