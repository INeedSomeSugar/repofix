from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit


def load_local_env(path: Path) -> None:
    """Read simple KEY=VALUE entries without overriding the process environment."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        name, value = name.strip(), value.strip().strip("\"'")
        if name.startswith(("DEEPSEEK_", "REPOFIX_")) and value:
            os.environ.setdefault(name, value)


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    api_key: str = field(default="", repr=False)
    base_url: str = "https://api.deepseek.com"
    model: str = ""
    request_timeout: float = 60.0

    @classmethod
    def from_env(cls, project_root: Path | None = None) -> Settings:
        root = (project_root or Path.cwd()).resolve()
        load_local_env(root / ".env")
        base = os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com").rstrip("/")
        parsed = urlsplit(base)
        if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError("DEEPSEEK_BASE_URL must be an HTTPS URL without embedded credentials")
        if parsed.query or parsed.fragment:
            raise ValueError("DEEPSEEK_BASE_URL must not contain query parameters or fragments")
        return cls(
            data_dir=Path(os.environ.get("REPOFIX_DATA_DIR", str(root / "work"))).resolve(),
            api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
            base_url=base,
            model=os.environ.get("DEEPSEEK_MODEL", ""),
        )
