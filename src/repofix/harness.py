"""Trusted subprocess entry point. Not exposed as an agent tool or editable file."""

import json
import sys
import unittest
from pathlib import Path


def main():
    repository = Path(sys.argv[1]).resolve()
    tests = Path(sys.argv[2]).resolve()
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(repository))
    suite = unittest.defaultTestLoader.discover(str(tests), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    payload = {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "unexpected_successes": len(result.unexpectedSuccesses),
        "expected_failures": len(result.expectedFailures),
        "passed": bool(
            result.wasSuccessful()
            and result.testsRun > 0
            and not result.skipped
            and not result.expectedFailures
        ),
    }
    # The parent reads this trusted side channel, never a marker printed by repository code.
    Path(sys.argv[3]).write_text(json.dumps(payload), encoding="utf-8")
    return 0 if payload["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
