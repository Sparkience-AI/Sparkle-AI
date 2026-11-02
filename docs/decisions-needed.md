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

## Capture behavior

Explicit user-invoked capture is now the only supported default. Decide whether passive clipboard
monitoring should be removed permanently or return later as an advanced, visibly active opt-in
mode. It must not return as the default.

## Cloud provider

Decide whether Gemini belongs in the first release or a later opt-in release. Before enabling it in
the UI, implement provider choice, payload preview, explicit consent, credential storage and
deletion, timeouts, cancellation, and fake-provider integration tests.
