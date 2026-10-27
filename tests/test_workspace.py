import json

import pytest

from repofix.engine import create_run
from repofix.tools import execute_tool
from repofix.workspace import PolicyError, Workspace, check_python


@pytest.mark.parametrize(
    "path",
    [
        "../independent_tests/test_heldout.py",
        "/etc/passwd",
        "C:/secrets.py",
        "project/../../hidden.py",
        ".env",
        "project\\core.py",
        "project/.secret.py",
        "project/core.py:stream",
        "project/core.txt",
        "",
    ],
)
def test_rejects_non_repository_and_secret_paths(store, path):
    state = create_run(store, "csv_records")
    with pytest.raises(PolicyError):
        Workspace(store.directory(state.run_id)).read_file(path)


@pytest.mark.parametrize(
    "source",
    [
        "import os",
        "import subprocess",
        "open('file')",
        "eval('1+1')",
        "from io import open as read_anything",
        "import io\nio.open('file')",
        "import unittest\nunittest.TestCase.run = lambda x: None",
        "import unittest\n@unittest.skip('pass')\nclass Test(unittest.TestCase):\n    pass",
        "x = object.__subclasses__()",
        "getattr(object, 'name')",
    ],
)
def test_conservative_python_policy_rejects_unsafe_or_bypass_operations(source):
    with pytest.raises(PolicyError):
        check_python(source, is_test=True)


def test_source_transaction_recovery_and_request_identity(store):
    state = create_run(store, "rolling_average")
    workspace = Workspace(store.directory(state.run_id))
    old = workspace.read_file("project/core.py")["content"]
    new = "def rolling_average(values, window):\n    return []\n"
    receipt = workspace.replace_text("crash_recovery", "project/core.py", old, new)
    recovered = workspace.replace_text("crash_recovery", "project/core.py", old, new)
    assert not receipt["recovered"] and recovered["recovered"]
    with pytest.raises(PolicyError, match="request mismatch"):
        workspace.replace_text("crash_recovery", "project/core.py", old, new + "\n")


def test_original_tests_and_readme_cannot_be_changed_by_tools(store):
    state = create_run(store, "csv_records")
    workspace = Workspace(store.directory(state.run_id))
    original = workspace.read_file("tests/test_public.py")["content"]
    with pytest.raises(PolicyError):
        workspace.replace_text("try_tests", "tests/test_public.py", original, "pass\n")
    with pytest.raises(PolicyError):
        workspace.write_test("try_tests", "tests/test_public.py", "pass\n")
    (workspace.root / "tests/test_public.py").write_text("pass\n", encoding="utf-8")
    with pytest.raises(PolicyError, match="protected"):
        workspace.verify_integrity(state.manifest)


def test_new_regression_test_and_diff_are_preserved(store):
    state = create_run(store, "csv_records")
    workspace = Workspace(store.directory(state.run_id))
    workspace.write_test("new_test", "tests/test_agent_empty.py", "import unittest\n")
    workspace.verify_integrity(state.manifest)
    assert "+import unittest" in workspace.diff()
    assert "independent_tests" not in json.dumps(workspace.list_files())


def test_tool_schemas_reject_extra_arguments_and_unknown_tools(store):
    state = create_run(store, "csv_records")
    workspace = Workspace(store.directory(state.run_id))
    result = execute_tool(
        workspace,
        {
            "id": "1",
            "function": {
                "name": "run_tests",
                "arguments": '{"command":"print secrets"}',
            },
        },
        state.manifest,
    )
    assert not result["ok"] and "print secrets" not in json.dumps(result)
    assert execute_tool(workspace, {"function": {"name": "shell"}}, state.manifest) == {
        "ok": False,
        "error": "unknown_tool",
    }
