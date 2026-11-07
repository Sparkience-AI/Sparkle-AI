# Source release checklist

1. Confirm the tag matches `pyproject.toml`; update release notes and known limitations.
2. Run locked formatting, lint, tests, wheel/sdist build, and installed launcher smoke tests on Windows with Python 3.11–3.13.
3. Exercise explicit capture, monitoring consent, secret rejection, every provider selection/clear path, cancellation, shutdown, accessible labels, keyboard traversal, and display scaling.
4. Confirm no keys, prompts, clipboard text, or response chunks enter logs, reports, artifacts, or environment variables.
5. Run the source-release-evidence workflow and attach the wheel, source archive, SHA-256 file, CycloneDX SBOM, and provenance manifest.
6. Verify source installation in a clean virtual environment and document rollback to the prior tag.

Only source and Python wheel artifacts are supported by this checklist.
