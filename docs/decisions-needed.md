# Product-owner decisions

Wave 2 deliberately does not make the following choices implicitly.

## GUI licensing and source redistribution

Keep dependency and project licensing under review for source redistribution.

## Supported Windows versions

The developer preview targets Windows 11. Decide whether Windows 10 receives a supported period or
whether the first release is Windows 11-only.

## Implemented product decisions

The original automatic clipboard workflow is retained as a visibly active, session-only opt-in;
explicit capture remains the default. Gemini, OpenAI, and Anthropic are available through explicit
provider selection, in-memory BYOK, editable model identifiers, visible provider state, a
cloud-transmission confirmation, and provider-specific clear-key actions.
Release review should verify the wording and Windows interaction, but these are no longer missing
functional capabilities.
