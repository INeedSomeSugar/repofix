from __future__ import annotations

import ast
import difflib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath

from .storage import atomic_json, sha256

MAX_FILE_CHARS = 32000
ALLOWED_IMPORTS = {
    "collections",
    "math",
    "decimal",
    "statistics",
    "re",
    "json",
    "datetime",
    "functools",
    "itertools",
    "typing",
    "csv",
    "io",
    "string",
    "project",
}
FORBIDDEN_CALLS = {
    "open",
    "exec",
    "eval",
    "compile",
    "input",
    "globals",
    "locals",
    "vars",
    "getattr",
    "setattr",
    "delattr",
    "breakpoint",
    "help",
    "dir",
    "exit",
    "quit",
}


class PolicyError(ValueError):
    pass


def check_python(source: str, is_test: bool = False) -> None:
    """Conservative guard for bundled pure-Python exercises; not a security sandbox."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise PolicyError(f"invalid Python syntax at line {exc.lineno}") from None
    allowed = ALLOWED_IMPORTS | ({"unittest"} if is_test else set())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(alias.name.split(".")[0] not in allowed for alias in node.names):
                raise PolicyError("import is outside the bundled-exercise allowlist")
        elif isinstance(node, ast.ImportFrom):
            if node.module == "io" and any(alias.name != "StringIO" for alias in node.names):
                raise PolicyError("only io.StringIO is permitted")
            if node.module and node.module.startswith("unittest."):
                raise PolicyError("unittest extensions and mocking are disabled")
            if node.level:
                if node.level != 1 or node.module not in {"core", "utils"}:
                    raise PolicyError("relative import is outside the exercise package")
            elif (node.module or "").split(".")[0] not in allowed:
                raise PolicyError("import is outside the bundled-exercise allowlist")
        elif isinstance(node, ast.Name):
            if node.id.startswith("__") and node.id != "__name__":
                raise PolicyError("reflective names are disabled")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") or node.attr in {
                "skipTest",
                "skip",
                "skipIf",
                "skipUnless",
                "expectedFailure",
                "load",
                "dump",
                "open",
                "read",
                "write",
                "mock",
            }:
                raise PolicyError("reflective, file, or test-bypass operation is disabled")
            if isinstance(node.ctx, (ast.Store, ast.Del)) and not (
                isinstance(node.value, ast.Name) and node.value.id == "self"
            ):
                raise PolicyError("module/class monkeypatching is disabled")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in FORBIDDEN_CALLS:
                raise PolicyError("dynamic execution and direct file access are disabled")


def content_manifest(root: Path) -> dict[str, str]:
    result = {}
    for path in sorted(root.rglob("*")):
        reparse = os.name == "nt" and (
            path.lstat().st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
        )
        if path.is_symlink() or reparse:
            raise PolicyError("symlinks and junctions are disabled")
        if path.is_file():
            result[path.relative_to(root).as_posix()] = sha256(path.read_bytes())
    return result


class Workspace:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir.resolve()
        self.root = self.run_dir / "repository"
        self.transactions = self.run_dir / "transactions"
        self.transactions.mkdir(exist_ok=True)

    def resolve(self, relative: str) -> Path:
        if not relative or not re.fullmatch(r"[A-Za-z0-9_./-]+", relative):
            raise PolicyError("use a repository-relative POSIX path")
        parts = PurePosixPath(relative).parts
        if PurePosixPath(relative).is_absolute() or any(
            part in {".", ".."} or part.startswith(".") for part in parts
        ):
            raise PolicyError("path traversal and hidden paths are disabled")
        path = self.root.joinpath(*parts)
        current = path
        while current != self.root.parent:
            if current.exists() or current.is_symlink():
                attributes = current.lstat()
                reparse = os.name == "nt" and (
                    attributes.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT
                )
                if current.is_symlink() or reparse:
                    raise PolicyError("symlinks and junctions are disabled")
            current = current.parent
        if not path.resolve().is_relative_to(self.root.resolve()):
            raise PolicyError("path escapes the repository")
        if path.suffix not in {".py", ".md"}:
            raise PolicyError("only Python and Markdown exercise files are readable")
        return path

    def list_files(self) -> dict:
        return {"files": sorted(content_manifest(self.root))}

    def read_file(self, path: str) -> dict:
        target = self.resolve(path)
        text = target.read_text(encoding="utf-8")
        return {
            "path": path,
            "content": text[:MAX_FILE_CHARS],
            "truncated": len(text) > MAX_FILE_CHARS,
        }

    def search_code(self, query: str) -> dict:
        if not query or len(query) > 200:
            raise PolicyError("search query must contain 1 to 200 characters")
        matches = []
        for path in self.list_files()["files"]:
            if not path.endswith(".py"):
                continue
            for number, line in enumerate(self.read_file(path)["content"].splitlines(), 1):
                if query.casefold() in line.casefold():
                    matches.append({"path": path, "line": number, "text": line[:300]})
                    if len(matches) >= 40:
                        return {"matches": matches, "truncated": True}
        return {"matches": matches, "truncated": False}

    def _commit(
        self,
        call_id: str,
        path: str,
        content: str,
        before_hash: str | None,
        request_sha256: str | None = None,
    ) -> dict:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,160}", call_id):
            raise PolicyError("invalid tool call id")
        if len(content) > MAX_FILE_CHARS:
            raise PolicyError("file exceeds the exercise size limit")
        check_python(content, is_test=path.startswith("tests/"))
        target = self.resolve(path)
        transaction = self.transactions / f"{call_id}.json"
        after_hash = sha256(content.encode("utf-8"))
        intent = {
            "path": path,
            "before_sha256": before_hash,
            "after_sha256": after_hash,
            "request_sha256": request_sha256,
        }
        if transaction.exists():
            previous = json.loads(transaction.read_text(encoding="utf-8"))
            if previous != intent:
                raise PolicyError("tool call id was reused for a different mutation")
        else:
            atomic_json(transaction, intent)
        current_hash = sha256(target.read_bytes()) if target.exists() else None
        if current_hash == after_hash:
            return {**intent, "recovered": True}
        if current_hash != before_hash:
            raise PolicyError("file changed since this tool transaction began")
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(".py.tmp")
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        return {**intent, "recovered": False}

    def replace_text(self, call_id: str, path: str, old: str, new: str) -> dict:
        if not re.fullmatch(r"project/[A-Za-z0-9_/-]+\.py", path):
            raise PolicyError("only existing project/*.py source files may be edited")
        target = self.resolve(path)
        transaction = self.transactions / f"{call_id}.json"
        signature = sha256(json.dumps([path, old, new], ensure_ascii=False).encode("utf-8"))
        if transaction.exists():
            intent = json.loads(transaction.read_text(encoding="utf-8"))
            if intent["path"] != path or intent.get("request_sha256") != signature:
                raise PolicyError("tool transaction request mismatch")
            if sha256(target.read_bytes()) == intent["after_sha256"]:
                return {**intent, "recovered": True}
        content = target.read_text(encoding="utf-8")
        if not old or old == new or content.count(old) != 1:
            raise PolicyError("old text must match exactly once and the replacement must change it")
        return self._commit(
            call_id,
            path,
            content.replace(old, new, 1),
            sha256(target.read_bytes()),
            signature,
        )

    def write_test(self, call_id: str, path: str, content: str) -> dict:
        if not re.fullmatch(r"tests/test_agent_[A-Za-z0-9_]+\.py", path):
            raise PolicyError("new tests must use tests/test_agent_<name>.py")
        target = self.resolve(path)
        original = self.run_dir / "original" / path
        if original.exists():
            raise PolicyError("original tests are immutable")
        transaction = self.transactions / f"{call_id}.json"
        before_hash = sha256(target.read_bytes()) if target.exists() else None
        if transaction.exists():
            before_hash = json.loads(transaction.read_text(encoding="utf-8"))["before_sha256"]
        return self._commit(call_id, path, content, before_hash)

    def verify_integrity(self, original_manifest: dict[str, str]) -> None:
        current = content_manifest(self.root)
        for path, digest in original_manifest.items():
            if not path.startswith("project/") and current.get(path) != digest:
                raise PolicyError("a protected original file was changed or removed")
            if path not in current:
                raise PolicyError("original files may not be removed")
        for path in current.keys() - original_manifest.keys():
            if not re.fullmatch(r"tests/test_agent_[A-Za-z0-9_]+\.py", path):
                raise PolicyError("unexpected file in the managed repository")
        for path in current:
            if path.endswith(".py"):
                check_python(self.read_file(path)["content"], is_test=path.startswith("tests/"))

    def diff(self) -> str:
        original = self.run_dir / "original"
        paths = set(content_manifest(original)) | set(content_manifest(self.root))
        lines = []
        for path in sorted(paths):
            old = (
                (original / path).read_text(encoding="utf-8") if (original / path).exists() else ""
            )
            new = (
                (self.root / path).read_text(encoding="utf-8")
                if (self.root / path).exists()
                else ""
            )
            lines.extend(
                difflib.unified_diff(
                    old.splitlines(keepends=True),
                    new.splitlines(keepends=True),
                    fromfile=f"a/{path}",
                    tofile=f"b/{path}",
                )
            )
        return "".join(lines)
