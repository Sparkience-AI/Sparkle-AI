# Security policy

## Reporting a vulnerability

Do not open a public issue for vulnerabilities involving clipboard disclosure, credentials,
provider routing, global hotkeys, dependency compromise, or arbitrary execution. Use GitHub's
private vulnerability reporting for this repository when available, or contact the maintainers
privately through the organization profile.

Include a minimal reproduction without real secrets or private clipboard data. Maintainers will
acknowledge the report, assess affected versions, and coordinate disclosure when a fix is ready.

## Supported versions

Sparkle AI is currently a pre-alpha developer preview with no supported binary release. Security
fixes are applied to the latest default branch only.

## Security boundaries

- Ollama is supported only on loopback by default.
- Clipboard processing must be explicitly invoked.
- Captured content and credentials must not appear in default logs.
- Cloud routing is not enabled in the current UI.
- Binary distribution is frozen pending the licensing and signing decisions.
