#!/usr/bin/env python3
"""Create a Firefox-compatible extension package from the LinkedIn clipper folder."""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EXTENSION_DIR = REPO_ROOT / "extensions" / "linkedin-job-clipper"
DEFAULT_OUTPUT = EXTENSION_DIR / "linkedin-job-clipper.xpi"


def build_xpi(output: Path, source_dir: Path = EXTENSION_DIR) -> Path:
    if not source_dir.exists():
        raise FileNotFoundError(f"Extension directory not found: {source_dir}")

    if not (source_dir / "manifest.json").exists():
        raise FileNotFoundError(f"manifest.json not found in: {source_dir}")

    output.parent.mkdir(parents=True, exist_ok=True)

    output = output.resolve()

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source_dir.rglob("*")):
            if not path.is_file():
                continue
            if path.resolve() == output:
                continue
            archive.write(path, arcname=path.relative_to(source_dir))

    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a Firefox-compatible .xpi package for the LinkedIn clipper.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output .xpi path.")
    args = parser.parse_args()

    try:
        output = build_xpi(args.output)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Created Firefox package: {output}")
    print("Tip: Firefox expects the archive to contain manifest.json at the root of the package.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
