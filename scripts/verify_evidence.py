import argparse
import hashlib
import json
from pathlib import Path


def verify(manifest_path: Path, report_path: Path) -> int:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if hashlib.sha256(report_path.read_bytes()).hexdigest() != manifest["report_sha256"]:
        raise ValueError("evaluation report hash mismatch")
    root = manifest_path.parent.resolve()
    for relative, expected in manifest["files"].items():
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError("manifest path escapes evidence directory")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f"evidence hash mismatch: {relative}")
    return len(manifest["files"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            {"verified_files": verify(args.manifest, args.report), "report_sha256_verified": True}
        )
    )
