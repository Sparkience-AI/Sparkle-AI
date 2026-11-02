# Privacy and data flow

## Default local route

1. The user copies text in another application.
2. Sparkle AI does nothing until the user presses `Ctrl+Shift+Space` or selects **Analyze
   clipboard now**.
3. Sparkle AI rejects empty, null-delimited, or oversized content.
4. The application sends the validated text to Ollama at `http://127.0.0.1:11434`.
5. The response is displayed in the in-memory overlay.

Sparkle AI does not intentionally persist captured text, prompts, or responses. It does not log
their contents by default. Ollama and the selected local model have their own behavior and should
be configured and audited separately.

## Cloud-provider boundary

The source includes an optional Gemini adapter, but the desktop UI does not enable cloud routing
in this release. A future cloud route must show the provider and payload preview, obtain explicit
consent, pass the key directly to the provider client, provide a clear-key action, and never write
the key or captured text to logs or process-global environment variables.

## Retention and deletion

The overlay retains the current response only for the running process. Closing the overlay cancels
the current application task where cooperative cancellation is possible. Exiting the tray
application clears in-memory state. There is no conversation database or analytics service.

## Known limitations

- Clipboard contents may already have been observed by the operating system or other applications.
- Provider cancellation is cooperative; a blocking provider call is bounded by its request timeout
  but may not stop immediately.
- Prompt-injection defenses reduce risk but cannot guarantee model behavior.
- Clipboard text may contain secrets. Users should inspect it before invoking analysis.
