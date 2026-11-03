# Product-owner decisions required before release

Wave 2 deliberately does not make the following choices implicitly.

## GUI licensing

Choose one reviewed path before binary distribution:

1. Keep PyQt6 with an appropriate commercial license.
2. Align the project licensing with the applicable PyQt GPLv3 obligations.
3. Perform a separately reviewed migration to PySide6 and comply with its license terms.

The current GPL-2.0 repository license plus PyQt6 dependency is not treated as distribution-ready.

## Windows distribution

Choose Microsoft Store MSIX, signed non-Store MSIX, or both. Self-signed packages are suitable only
for controlled testing. Install, upgrade, uninstall, settings preservation, and rollback must be
tested on clean supported Windows environments.

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
