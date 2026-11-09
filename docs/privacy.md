# Privacy and data flow

## Capture modes

- **Explicit capture (default):** Sparkle AI reads clipboard text only after `Ctrl+Shift+Space` or
  **Analyze clipboard now**.
- **Automatic monitoring (opt-in):** the user enables a visibly checked tray action and confirms
  the current provider. Clipboard changes are debounced and deduplicated. Blank, binary,
  oversized, and likely-credential content is skipped automatically with a local tray notice.

Monitoring is disabled at every process start. Pausing the assistant stops pending automatic
capture. The feature uses the normal user application process; it does not install a Windows
service or start at login.

## Provider routes

- **Local Ollama (default):** validated text is sent only to the loopback endpoint
  `http://127.0.0.1:11434`.
- **Google Gemini (opt-in):** the user installs the optional dependency, enters their own key, and
  confirms that captured text and follow-up messages will be sent to Google. The active cloud
  provider is visible in the tray tooltip and overlay.
- **OpenAI (opt-in):** the user supplies an OpenAI key and model. Requests use the Responses API
  with response storage disabled by Sparkle AI.
- **Anthropic Claude (opt-in):** the user supplies an Anthropic key and model. Requests use the
  streaming Messages API.

Sparkle AI does not intentionally persist captured text, prompts, or responses. It does not log
their contents by default. Ollama and the selected local model have their own behavior and should
be configured and audited separately.

Cloud keys are passed directly to their provider clients, retained only in process memory, and
removed by the matching **Clear … API key** action or application exit. They are never copied into
a process-global environment variable or application log. Selecting a provider and enabling
automatic monitoring are separate consent decisions. Provider-side retention and account policy
remain governed by the selected provider and the user's account configuration.

## Retention and deletion

The overlay retains the current response only for the running process. Closing it with the button,
clicking outside it, or disabling the assistant follows one cancellation lifecycle: deferred starts
are removed, queued output is ignored, and the current task is signalled to stop between provider
chunks. Every fresh capture starts with an empty response and follow-up context. Changing the
provider, cloud key, or cloud model cancels current work and clears that context before reuse.
Exiting is deferred while a blocking local provider call is still stopping, preventing unsafe
worker destruction. Exiting the tray application clears in-memory state. There is no conversation
database or analytics service.

## Known limitations

- Clipboard contents may already have been observed by the operating system or other applications.
- Provider cancellation is cooperative; a blocking provider call is bounded by its request timeout
  but may not stop immediately.
- Prompt-injection defenses reduce risk but cannot guarantee model behavior.
- Secret detection is heuristic and cannot identify every credential. Explicit capture can still
  transmit sensitive text, so users should inspect clipboard contents and the visible provider.
