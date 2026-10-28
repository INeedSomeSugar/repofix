"""Export only completed, bundled-exercise runs; never export arbitrary workspace files."""

import argparse
import json
from pathlib import Path

from repofix.cases import case_fingerprint, get_case
from repofix.schema import RunState
from repofix.storage import sha256, utc_now
from repofix.workspace import Workspace


def export(report_path: Path, destination: Path, run_root: Path):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if destination.exists():
        raise ValueError("evidence destination exists; choose a new directory")
    destination.mkdir(parents=True)
    copied = {}
    for item in report["runs"]:
        run_id = item["run_id"]
        if len(run_id) != 32 or any(char not in "0123456789abcdef" for char in run_id):
            raise ValueError("invalid run id")
        source = run_root / run_id
        state = RunState.model_validate_json((source / "run.json").read_text(encoding="utf-8"))
        if state.status not in {
            "verified",
            "failed",
            "error",
            "budget_exhausted",
            "needs_review",
            "stalled",
        }:
            raise ValueError("only finished runs may be exported")
        if case_fingerprint(get_case(state.case_id)) != state.case_sha256:
            raise ValueError("bundled exercise fingerprint mismatch")
        Workspace(source).verify_integrity(state.manifest)
        for filename in (
            "run.json",
            "events.jsonl",
            "patch.diff",
            "summary.md",
            "provider-metadata.jsonl",
        ):
            path = source / filename
            if not path.exists():
                continue
            data = path.read_bytes()
            if filename == "patch.diff" and sha256(data) != item["patch_sha256"]:
                raise ValueError("patch does not match the original evaluation report")
            relative = f"{run_id}/{filename}"
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            copied[relative] = sha256(data)
        # Include only managed Python/Markdown snapshots, never env files or host logs.
        for folder in ("original", "repository", "checkpoints"):
            root = source / folder
            for path in sorted(root.rglob("*")):
                if not path.is_file() or (
                    path.suffix not in {".py", ".md"}
                    and not (folder == "checkpoints" and path.name == "manifest.json")
                ):
                    continue
                relative = f"{run_id}/{folder}/{path.relative_to(root).as_posix()}"
                target = destination / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
                copied[relative] = sha256(target.read_bytes())
    manifest = {
        "created_at": utc_now(),
        "report_name": report_path.name,
        "report_sha256": sha256(report_path.read_bytes()),
        "scope": "Completed fixed trusted development tasks; no keys or private repositories",
        "files": copied,
    }
    (destination / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {"runs": len(report["runs"]), "files": len(copied), "destination": str(destination)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--run-root", type=Path, default=Path("work/runs"))
    args = parser.parse_args()
    print(json.dumps(export(args.report, args.out, args.run_root), ensure_ascii=False))


if __name__ == "__main__":
    main()
