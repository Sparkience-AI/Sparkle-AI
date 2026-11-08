"""Generate checksums, a CycloneDX environment SBOM, and source-build provenance."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import sys
from datetime import UTC, datetime
from pathlib import Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_evidence(dist: Path, output: Path, project: str, version: str) -> None:
    artifacts = sorted([*dist.glob("*.whl"), *dist.glob("*.tar.gz")])
    if not artifacts:
        raise ValueError("No wheel or source distribution was found.")
    output.mkdir(parents=True, exist_ok=True)
    checksums = {artifact.name: _sha256(artifact) for artifact in artifacts}
    (output / "SHA256SUMS.json").write_text(
        json.dumps(checksums, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    components = []
    for distribution in sorted(
        importlib.metadata.distributions(), key=lambda item: item.metadata["Name"].lower()
    ):
        name = distribution.metadata["Name"]
        components.append(
            {
                "type": "library",
                "name": name,
                "version": distribution.version,
                "purl": f"pkg:pypi/{name.lower().replace('_', '-')}@{distribution.version}",
            }
        )
    (output / "sbom.cdx.json").write_text(
        json.dumps(
            {
                "bomFormat": "CycloneDX",
                "specVersion": "1.5",
                "version": 1,
                "metadata": {
                    "component": {"type": "application", "name": project, "version": version}
                },
                "components": components,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (output / "provenance.json").write_text(
        json.dumps(
            {
                "project": project,
                "version": version,
                "source_revision": os.environ.get("GITHUB_SHA", "local"),
                "workflow_run": os.environ.get("GITHUB_RUN_ID", "local"),
                "generated_at": datetime.now(UTC).isoformat(),
                "python": platform.python_version(),
                "platform": platform.platform(),
                "artifacts": checksums,
                "distribution_scope": "source-and-wheel-only",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args(argv)
    try:
        build_evidence(args.dist, args.output, args.project, args.version)
    except ValueError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
