# Windows developer setup

## Supported preview environment

- Windows 11
- Python 3.11–3.13
- uv
- Ollama listening on loopback only

Install the locked environment and local model:

```powershell
uv sync --locked
ollama pull llama3.2:3b
uv run --locked sparkle-ai
```

Install optional cloud integrations with `uv sync --locked --extra gemini`,
`uv sync --locked --extra openai`, or `uv sync --locked --extra anthropic`. The provider menu asks
for a session key and editable model identifier. Keys remain in process memory only.

The global hotkey library may require permissions allowed by the local Windows security policy.
If the hotkey conflicts with another application, exit Sparkle AI from the tray. Configurable
hotkeys are planned but not yet implemented.

Automatic monitoring is off at startup. Enable **Monitor clipboard automatically** from the tray
only when the visible provider and clipboard contents are appropriate. The tray tooltip reports
the active provider and monitoring state.

## Troubleshooting

- **No response:** confirm `ollama list` includes `llama3.2:3b` and the daemon is running.
- **Hotkey does nothing:** use **Analyze clipboard now** from the tray and check for a system hotkey
  conflict.
- **Payload rejected:** select plain text shorter than 20,000 characters.
- **Application does not start:** run from a terminal with the locked uv environment and report the
  exception without including clipboard contents or credentials.
- **Cloud provider unavailable:** install its matching optional extra, verify the model identifier
  is available to the API account, and re-enter the session key.

There is no supported installer, signing certificate, automatic update channel, or Windows 10
compatibility claim in this preview.
