"""Build three MIT-licensed, commit-pinned function excerpts; never execute downloads."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
from textwrap import dedent
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = "https://github.com/more-itertools/more-itertools"
SOURCE_PATH = "more_itertools/more.py"
SPECS = [
    {
        "id": "upstream_value_chain",
        "fix": "7847d4324a581da8d0919734a8e50b2a6573b780",
        "base": "bc8be1013ac90fe3c1df8aae646b02605d578818",
        "functions": ["value_chain"],
        "title": "more-itertools：迭代期间的TypeError被误当作标量",
        "issue": "修复value_chain：字符串和bytes仍原样输出；不可迭代参数作为标量；"
        "已经开始消费的迭代器若抛出TypeError，必须向调用者传播，不能吞掉错误或输出该迭代器。",
        "public": """
            import unittest
            from project.core import value_chain

            class Public(unittest.TestCase):
                def test_mixed(self):
                    actual = list(value_chain(1, [2, 3], 'ab', b'cd'))
                    self.assertEqual(actual, [1, 2, 3, 'ab', b'cd'])
                def test_error_during_consumption(self):
                    result = value_chain(map(len, ['ab', 7]))
                    self.assertEqual(next(result), 2)
                    with self.assertRaises(TypeError):
                        next(result)
        """,
        "heldout": """
            import unittest
            from project.core import value_chain

            class Independent(unittest.TestCase):
                def test_late_error(self):
                    def broken():
                        yield 11
                        raise TypeError('late')
                    result = value_chain(broken(), 99)
                    self.assertEqual(next(result), 11)
                    with self.assertRaisesRegex(TypeError, 'late'):
                        next(result)
                def test_noniterable(self):
                    class Scalar:
                        def __iter__(self):
                            raise TypeError('scalar')
                    obj = Scalar()
                    self.assertEqual(list(value_chain(obj, [1])), [obj, 1])
                def test_empty_and_nested(self):
                    self.assertEqual(list(value_chain()), [])
                    self.assertEqual(list(value_chain([], [[1]], '')), [[1], ''])
        """,
    },
    {
        "id": "upstream_split_empty",
        "fix": "ce676d24136e6efa932df8a4f3bf4801b89e1dd0",
        "base": "d92f081a089714e0aa92434c797fdd1a06da1290",
        "functions": ["split_before", "split_after", "split_when"],
        "title": "more-itertools：maxsplit=0时空输入产生额外空分组",
        "issue": "修复split_before、split_after、split_when：空输入在maxsplit=0时也应产生零个分组；"
        "非空输入在maxsplit=0时仍产生包含全部内容的一组。保留各自原有拆分位置、惰性迭代与maxsplit语义。",
        "public": """
            import unittest
            from project.core import split_before, split_after, split_when

            class Public(unittest.TestCase):
                def test_empty_zero(self):
                    functions = [(split_before, bool), (split_after, bool),
                                 (split_when, lambda a, b: a != b)]
                    for func, pred in functions:
                        with self.subTest(function=func):
                            self.assertEqual(list(func(iter([]), pred, maxsplit=0)), [])
                def test_nonempty_zero(self):
                    functions = [(split_before, bool), (split_after, bool),
                                 (split_when, lambda a, b: True)]
                    for func, pred in functions:
                        self.assertEqual(list(func(iter([1, 2]), pred, maxsplit=0)), [[1, 2]])
        """,
        "heldout": """
            import unittest
            from project.core import split_before, split_after, split_when

            class Independent(unittest.TestCase):
                def test_empty_all_limits(self):
                    for limit in [-1, 0, 1, 3]:
                        self.assertEqual(list(split_before('', bool, limit)), [])
                        self.assertEqual(list(split_after([], bool, limit)), [])
                        self.assertEqual(list(split_when(iter([]), lambda a, b: True, limit)), [])
                def test_original_boundaries(self):
                    result = split_before(range(4), lambda x: x % 2 == 0)
                    self.assertEqual(list(result), [[0, 1], [2, 3]])
                    result = split_after(range(4), lambda x: x % 2 == 0)
                    self.assertEqual(list(result), [[0], [1, 2], [3]])
                    result = split_when([1, 1, 2, 2, 3], lambda a, b: a != b)
                    self.assertEqual(list(result), [[1, 1], [2, 2], [3]])
                def test_one_split(self):
                    result = split_after(range(5), lambda x: x % 2 == 0, 1)
                    self.assertEqual(list(result), [[0], [1, 2, 3, 4]])
                    result = split_before(range(6), lambda x: x % 2 == 0, 1)
                    self.assertEqual(list(result), [[0, 1], [2, 3, 4, 5]])
        """,
    },
    {
        "id": "upstream_custom_exception",
        "fix": "def2dabea858b6ecb84ee0c52e6e07929f2c409c",
        "base": "9ed3dbb0ae527230cd156d91d0af305478558fba",
        "functions": ["one", "only"],
        "title": "more-itertools：假值自定义异常被默认异常覆盖",
        "issue": "修复one和only：用户提供的too_short/too_long异常即使布尔值为False也必须被抛出。"
        "指定自定义too_long时不要构造含元素repr的默认消息，避免元素的repr错误覆盖自定义异常。"
        "保留单元素返回、one空输入异常和only空输入default行为。",
        "public": """
            import unittest
            from project.core import one, only

            class FalsyError(Exception):
                def __bool__(self):
                    return False

            class Public(unittest.TestCase):
                def test_custom_long(self):
                    for func in [one, only]:
                        with self.assertRaises(FalsyError):
                            func([1, 2], too_long=FalsyError('many'))
                def test_custom_short(self):
                    with self.assertRaises(FalsyError):
                        one([], too_short=FalsyError('few'))
                def test_single(self):
                    self.assertEqual(one([7]), 7)
                    self.assertEqual(only([7]), 7)
        """,
        "heldout": """
            import unittest
            from project.core import one, only

            class NoRepr:
                def __repr__(self):
                    raise RuntimeError('repr must not be evaluated')

            class Independent(unittest.TestCase):
                def test_no_repr_with_custom_exception(self):
                    for func in [one, only]:
                        with self.assertRaises(OverflowError):
                            func([NoRepr(), NoRepr()], too_long=OverflowError)
                def test_exception_identity(self):
                    error = LookupError('same instance')
                    for func in [one, only]:
                        try:
                            func([1, 2], too_long=error)
                        except LookupError as caught:
                            self.assertIs(caught, error)
                        else:
                            self.fail('did not raise')
                def test_defaults(self):
                    self.assertEqual(only([], default='missing'), 'missing')
                    with self.assertRaises(ValueError):
                        one([])
                    with self.assertRaises(ValueError):
                        only([1, 2])
        """,
    },
]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def excerpt(data: bytes, names: list[str]) -> tuple[str, list[dict]]:
    text = data.decode("utf-8")
    lines = text.splitlines(keepends=True)
    nodes = {node.name: node for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}
    parts, spans = [], []
    for name in names:
        node = nodes[name]
        part = "".join(lines[node.lineno - 1 : node.end_lineno])
        parts.append(part)
        spans.append(
            {
                "name": name,
                "first_line": node.lineno,
                "last_line": node.end_lineno,
                "sha256": digest(part.encode()),
            }
        )
    return "\n\n".join(parts), spans


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch", action="store_true", help="download fixed public snapshots only")
    args = parser.parse_args()
    cache = ROOT / "work/upstream"
    cache.mkdir(parents=True, exist_ok=True)
    cases = []
    license_ref = SPECS[0]["fix"]
    license_path = cache / "LICENSE"
    if args.fetch:
        url = (
            f"https://raw.githubusercontent.com/more-itertools/more-itertools/{license_ref}/LICENSE"
        )
        with urlopen(url, timeout=30) as response:
            license_path.write_bytes(response.read(1_000_000))
    license_text = license_path.read_text("utf-8")
    for spec in SPECS:
        sources = []
        metadata = []
        for kind in ["base", "fix"]:
            ref = spec[kind]
            path = cache / (ref + "-more.py")
            url = f"https://raw.githubusercontent.com/more-itertools/more-itertools/{ref}/{SOURCE_PATH}"
            if args.fetch:
                with urlopen(url, timeout=30) as response:
                    path.write_bytes(response.read(2_000_000))
            data = path.read_bytes()
            functions, spans = excerpt(data, spec["functions"])
            header = f"# Excerpt from more-itertools {ref}; MIT License.\n"
            sources.append(header + functions)
            metadata.append(
                {
                    "commit": ref,
                    "url": url,
                    "upstream_file_sha256": digest(data),
                    "functions": spans,
                    "core_sha256": digest(sources[-1].encode()),
                }
            )
        # The header is metadata, not part of the repair; preserve the base header in both versions.
        sources[1] = sources[0].splitlines(keepends=True)[0] + "".join(
            sources[1].splitlines(keepends=True)[1:]
        )
        metadata[1]["core_sha256"] = digest(sources[1].encode())
        public, heldout = (dedent(spec[key]).lstrip("\n") for key in ["public", "heldout"])
        cases.append(
            {
                "id": spec["id"],
                "title": spec["title"],
                "category": "upstream_excerpt",
                "difficulty": "curated-development",
                "issue": spec["issue"],
                "files": {
                    "project/__init__.py": "",
                    "project/core.py": sources[0],
                    "tests/test_public.py": public,
                    "README.md": (
                        f"# {spec['title']}\n\n{spec['issue']}\n\n"
                        "MIT-licensed function excerpt. See LICENSE.md.\n"
                    ),
                    "LICENSE.md": license_text,
                },
                "heldout": heldout,
                "replay_edits": [{"path": "project/core.py", "old": sources[0], "new": sources[1]}],
                "provenance": {
                    "kind": "upstream_function_excerpt",
                    "repository": UPSTREAM,
                    "fix_url": UPSTREAM + "/commit/" + spec["fix"],
                    "license": "MIT",
                    "license_ref": license_ref,
                    "license_sha256": digest(license_text.encode()),
                    "snapshots": metadata,
                    "adaptation": (
                        "Unmodified AST-located function excerpts plus attribution header; "
                        "tests locally authored from upstream regression conditions."
                    ),
                    "evaluation_scope": (
                        "retrospective curated development; not full-repository or unseen benchmark"
                    ),
                    "public_tests_sha256": digest(public.encode()),
                    "independent_tests_sha256": digest(heldout.encode()),
                },
            }
        )
    destination = ROOT / "src/repofix/fixtures/upstream.json"
    destination.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", "utf-8")
    license_out = ROOT / "third_party/more-itertools/LICENSE"
    license_out.parent.mkdir(parents=True, exist_ok=True)
    license_out.write_text(license_text, "utf-8")
    print(
        json.dumps(
            {
                "cases": len(cases),
                "output": str(destination),
                "fixture_sha256": digest(destination.read_bytes()),
            }
        )
    )


if __name__ == "__main__":
    main()
