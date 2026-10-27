from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, StrictStr, ValidationError

from .runner import run_tests
from .workspace import PolicyError, Workspace


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EmptyArgs(Arguments):
    pass


class ReadArgs(Arguments):
    path: StrictStr = Field(max_length=150)


class SearchArgs(Arguments):
    query: StrictStr = Field(min_length=1, max_length=200)


class ReplaceArgs(ReadArgs):
    old: StrictStr = Field(min_length=1, max_length=32000)
    new: StrictStr = Field(max_length=32000)


class TestArgs(ReadArgs):
    content: StrictStr = Field(max_length=32000)


TOOL_TYPES = {
    "list_files": (EmptyArgs, "List visible files in the managed repository."),
    "read_file": (ReadArgs, "Read a Python or Markdown file using a relative POSIX path."),
    "search_code": (
        SearchArgs,
        "Search a literal substring in Python source; returns line numbers.",
    ),
    "replace_text": (
        ReplaceArgs,
        "Edit an existing project/*.py file; old must match exactly once.",
    ),
    "write_test": (TestArgs, "Create/update your own tests/test_agent_<name>.py regression test."),
    "run_tests": (
        EmptyArgs,
        "Execute all public and agent-added tests and inspect actual failures.",
    ),
}


def tool_schemas() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": model.model_json_schema(),
            },
        }
        for name, (model, description) in TOOL_TYPES.items()
    ]


def execute_tool(
    workspace: Workspace,
    call: dict,
    manifest: dict[str, str],
    timeout: float = 12.0,
    test_runner=None,
) -> dict:
    name = call.get("function", {}).get("name")
    if name not in TOOL_TYPES:
        return {"ok": False, "error": "unknown_tool"}
    try:
        raw = call["function"].get("arguments", "{}")
        if not isinstance(raw, str) or len(raw) > 70000:
            raise PolicyError("tool arguments exceed the size limit")
        args = TOOL_TYPES[name][0].model_validate_json(raw).model_dump()
        workspace.verify_integrity(manifest)
        if name in {"replace_text", "write_test"}:
            result = getattr(workspace, name)(call["id"], **args)
        elif name == "run_tests":
            result = (test_runner or run_tests)(
                workspace.root,
                workspace.root / "tests",
                workspace.run_dir / "logs",
                timeout=timeout,
            )
        else:
            result = getattr(workspace, name)(**args)
        return {"ok": True, **result}
    except (PolicyError, ValidationError, FileNotFoundError, UnicodeError) as exc:
        # ValidationError may embed user input; expose only its type.
        detail = str(exc) if isinstance(exc, PolicyError) else type(exc).__name__
        return {"ok": False, "error": "tool_rejected", "detail": detail}
    except (OSError, KeyError, ValueError):
        return {"ok": False, "error": "tool_execution_error"}
