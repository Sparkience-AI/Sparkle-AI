from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.release_evidence import build_evidence


def test_release_evidence_is_source_only_and_hashed(tmp_path: Path, monkeypatch) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    wheel = dist / "sparkle_ai-0.1.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel")
    monkeypatch.setenv("GITHUB_SHA", "abc123")
    output = tmp_path / "evidence"
    build_evidence(dist, output, "sparkle-ai", "0.1.0")
    checksums = json.loads((output / "SHA256SUMS.json").read_text(encoding="utf-8"))
    assert checksums[wheel.name] == hashlib.sha256(b"wheel").hexdigest()
    assert json.loads((output / "sbom.cdx.json").read_text())["bomFormat"] == "CycloneDX"
    provenance = json.loads((output / "provenance.json").read_text())
    assert provenance["source_revision"] == "abc123"
    assert provenance["distribution_scope"] == "source-and-wheel-only"
