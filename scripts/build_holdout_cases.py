"""Build three prospective synthetic tasks before first model exposure, without model calls."""

import json
from pathlib import Path
from textwrap import dedent

from repofix.storage import sha256


def clean(text):
    return dedent(text).lstrip()


def build():
    specs = [
        (
            "holdout_cursor_page",
            "事件游标分页的同序号边界",
            "修复project.core.page(events, limit, after=None)。events是可迭代事件字典，"
            "sequence为整数，event_id为唯一字符串。按(sequence,event_id)升序分页；"
            "after是二元素序列，严格返回大于该复合键的事件，游标不必对应已有事件。"
            "limit须为1至100的整数且不能是bool，否则ValueError。返回{'items':列表,"
            "'next_cursor':游标或None}；仅还有后续记录时next_cursor为本页末条的"
            "[sequence,event_id]，否则None。输入为空或游标之后无记录时返回空items和None。"
            "不得修改输入列表或事件；每个返回事件须为浅拷贝。",
            """
            def page(events, limit, after=None):
                events.sort(key=lambda row: row['sequence'])
                selected = events[:limit]
                if after is not None:
                    selected = [row for row in selected if row['sequence'] > after[0]]
                cursor = [selected[-1]['sequence'], selected[-1]['event_id']] if selected else None
                return {'items': selected, 'next_cursor': cursor}
            """,
            """
            def page(events, limit, after=None):
                if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 100:
                    raise ValueError('invalid limit')
                rows = sorted(events, key=lambda row: (row['sequence'], row['event_id']))
                if after is not None:
                    rows = [row for row in rows
                            if (row['sequence'], row['event_id']) > tuple(after)]
                selected = rows[:limit]
                cursor = None
                if len(rows) > limit:
                    cursor = [selected[-1]['sequence'], selected[-1]['event_id']]
                return {'items': [dict(row) for row in selected], 'next_cursor': cursor}
            """,
            """
            import unittest
            from project.core import page
            class PublicTests(unittest.TestCase):
                def test_same_sequence_and_terminal_cursor(self):
                    rows = [{'sequence': 2, 'event_id': 'c'}, {'sequence': 1, 'event_id': 'b'},
                            {'sequence': 1, 'event_id': 'a'}]
                    first = page(rows, 1)
                    self.assertEqual(first['next_cursor'], [1, 'a'])
                    last = page(rows, 2, [1, 'a'])
                    self.assertEqual([r['event_id'] for r in last['items']], ['b', 'c'])
                    self.assertIsNone(last['next_cursor'])
                def test_invalid_limit(self):
                    with self.assertRaises(ValueError):
                        page([], 0)
            """,
            """
            import unittest
            from project.core import page
            class IndependentTests(unittest.TestCase):
                def test_iterator_and_absent_cursor(self):
                    rows = ({'sequence': n, 'event_id': str(n)} for n in [4, 1, 3])
                    result = page(rows, 2, [2, 'missing'])
                    self.assertEqual([r['sequence'] for r in result['items']], [3, 4])
                    self.assertIsNone(result['next_cursor'])
                def test_nonmutation_and_shallow_copy(self):
                    rows = [{'sequence': 8, 'event_id': 'z'}, {'sequence': 1, 'event_id': 'a'}]
                    result = page(rows, 1)
                    self.assertEqual([r['sequence'] for r in rows], [8, 1])
                    result['items'][0]['event_id'] = 'changed'
                    self.assertEqual(rows[1]['event_id'], 'a')
                def test_empty_and_exhausted(self):
                    self.assertEqual(page([], 1), {'items': [], 'next_cursor': None})
                    row = {'sequence': 1, 'event_id': 'a'}
                    self.assertEqual(page([row], 1, [1, 'a']), {'items': [], 'next_cursor': None})
                def test_limit_types(self):
                    for limit in [True, False, -1, 101, 1.5, '2']:
                        with self.subTest(limit=limit), self.assertRaises(ValueError):
                            page([], limit)
            """,
        ),
        (
            "holdout_inventory_batch",
            "库存批量变更的原子性与版本检查",
            "修复project.core.apply_batch(stock, versions, changes)。stock和versions是已有SKU"
            "到非负整数库存和版本的字典。changes是可迭代字典，每项含sku、delta、"
            "expected_version。按顺序应用；同SKU后续操作须基于前一次递增后的版本检查。"
            "delta为整数（可为0），expected_version为非负整数，两者不接受bool；"
            "无效参数、版本不匹配或变更后库存负数抛ValueError，未知sku抛KeyError。"
            "每项成功变更版本加1。成功返回(new_stock,new_versions)，两字典都须为新对象；"
            "无论中途失败还是成功，均不得修改任何输入字典或changes中的对象。空变更也返回副本。",
            """
            def apply_batch(stock, versions, changes):
                for change in changes:
                    sku = change['sku']
                    stock[sku] += change['delta']
                    if versions[sku] != change['expected_version'] or stock[sku] < 0:
                        raise ValueError('conflict')
                    versions[sku] += 1
                return stock, versions
            """,
            """
            def apply_batch(stock, versions, changes):
                new_stock, new_versions = dict(stock), dict(versions)
                for change in changes:
                    sku = change['sku']
                    delta, expected = change['delta'], change['expected_version']
                    if not isinstance(delta, int) or isinstance(delta, bool):
                        raise ValueError('invalid delta')
                    if not isinstance(expected, int) or isinstance(expected, bool) or expected < 0:
                        raise ValueError('invalid expected_version')
                    if sku not in new_stock or sku not in new_versions:
                        raise KeyError(sku)
                    if new_versions[sku] != expected or new_stock[sku] + delta < 0:
                        raise ValueError('conflict')
                    new_stock[sku] += delta
                    new_versions[sku] += 1
                return new_stock, new_versions
            """,
            """
            import unittest
            from project.core import apply_batch
            class PublicTests(unittest.TestCase):
                def test_success_does_not_mutate(self):
                    stock, versions = {'A': 5}, {'A': 2}
                    result = apply_batch(stock, versions,
                                         [{'sku': 'A', 'delta': -2, 'expected_version': 2}])
                    self.assertEqual(result, ({'A': 3}, {'A': 3}))
                    self.assertEqual((stock, versions), ({'A': 5}, {'A': 2}))
                def test_failure_is_atomic(self):
                    stock, versions = {'A': 5}, {'A': 0}
                    with self.assertRaises(ValueError):
                        apply_batch(stock, versions,
                                    [{'sku': 'A', 'delta': -8, 'expected_version': 0}])
                    self.assertEqual(stock, {'A': 5})
            """,
            """
            import unittest
            from project.core import apply_batch
            class IndependentTests(unittest.TestCase):
                def test_repeated_sku_and_zero_delta(self):
                    changes = [{'sku': 'A', 'delta': -2, 'expected_version': 3},
                               {'sku': 'A', 'delta': 0, 'expected_version': 4}]
                    result = apply_batch({'A': 2}, {'A': 3}, iter(changes))
                    self.assertEqual(result, ({'A': 0}, {'A': 5}))
                    self.assertEqual(changes[1]['expected_version'], 4)
                def test_late_conflict_preserves_every_input(self):
                    for last in [{'sku': 'B', 'delta': -9, 'expected_version': 0},
                                 {'sku': 'A', 'delta': 1, 'expected_version': 0},
                                 {'sku': 'missing', 'delta': 1, 'expected_version': 0}]:
                        stock, versions = {'A': 2, 'B': 3}, {'A': 0, 'B': 0}
                        with self.assertRaises((ValueError, KeyError)):
                            apply_batch(stock, versions,
                                        [{'sku': 'A', 'delta': 1, 'expected_version': 0}, last])
                        self.assertEqual((stock, versions), ({'A': 2, 'B': 3}, {'A': 0, 'B': 0}))
                def test_reject_boolean_and_noninteger(self):
                    for field, value in [('delta', True), ('delta', 1.5),
                                         ('expected_version', False), ('expected_version', -1)]:
                        change = {'sku': 'A', 'delta': 1, 'expected_version': 0}
                        change[field] = value
                        with self.assertRaises(ValueError):
                            apply_batch({'A': 2}, {'A': 0}, [change])
                def test_empty_returns_distinct_copies(self):
                    stock, versions = {'A': 2}, {'A': 0}
                    result = apply_batch(stock, versions, [])
                    self.assertIsNot(result[0], stock)
                    self.assertIsNot(result[1], versions)
                    self.assertEqual(result, (stock, versions))
            """,
        ),
        (
            "holdout_money_allocation",
            "整数金额按权重分配与余数守恒",
            "修复project.core.allocate_cents(total, weights)。total是任意大小的整数分金额，"
            "可为负且不能为bool；weights是可迭代的非负整数权重，不接受bool。使用最大余数法："
            "先按abs(total)比例向下分配，再按精确余数从大到小补1分，余数相同按原始索引升序。"
            "最后统一恢复total符号，返回与权重顺序一致的整数列表，合计必须等于total。"
            "非空weights的权重总和须大于0。空weights仅当total=0时返回[]，否则ValueError。"
            "其他无效类型或负权重也抛ValueError，不修改输入，整个计算不得使用浮点近似。",
            """
            def allocate_cents(total, weights):
                denominator = sum(weights)
                return [int(total * weight / denominator) for weight in weights]
            """,
            """
            def allocate_cents(total, weights):
                if not isinstance(total, int) or isinstance(total, bool):
                    raise ValueError('invalid total')
                weights = list(weights)
                if any(not isinstance(w, int) or isinstance(w, bool) or w < 0 for w in weights):
                    raise ValueError('invalid weight')
                if not weights:
                    if total == 0:
                        return []
                    raise ValueError('empty weights')
                denominator = sum(weights)
                if denominator <= 0:
                    raise ValueError('zero weight sum')
                parts = [divmod(abs(total) * w, denominator) for w in weights]
                result = [part[0] for part in parts]
                order = sorted(range(len(weights)), key=lambda i: (-parts[i][1], i))
                for index in order[:abs(total) - sum(result)]:
                    result[index] += 1
                sign = -1 if total < 0 else 1
                return [sign * value for value in result]
            """,
            """
            import unittest
            from project.core import allocate_cents
            class PublicTests(unittest.TestCase):
                def test_conservation_and_ties(self):
                    self.assertEqual(allocate_cents(10, [1, 1, 1]), [4, 3, 3])
                    self.assertEqual(allocate_cents(2, [1, 1, 1]), [1, 1, 0])
                def test_negative(self):
                    self.assertEqual(allocate_cents(-5, [1, 2]), [-2, -3])
            """,
            """
            import unittest
            from project.core import allocate_cents
            class IndependentTests(unittest.TestCase):
                def test_exact_large_integer(self):
                    self.assertEqual(allocate_cents(9007199254740993, [1]), [9007199254740993])
                    self.assertEqual(allocate_cents(7, [0, 2, 1]), [0, 5, 2])
                def test_iterator_and_nonmutation(self):
                    weights = [1, 4, 2]
                    self.assertEqual(allocate_cents(11, iter(weights)), [2, 6, 3])
                    self.assertEqual(weights, [1, 4, 2])
                def test_zero_and_empty(self):
                    self.assertEqual(allocate_cents(0, []), [])
                    self.assertEqual(allocate_cents(0, [0, 1]), [0, 0])
                    for total, weights in [(2, []), (0, [0, 0]), (1, [-1, 2])]:
                        with self.assertRaises(ValueError):
                            allocate_cents(total, weights)
                def test_invalid_types(self):
                    for total, weights in [(True, [1]), (1.5, [1]), (1, [True]), (1, [1.5])]:
                        with self.assertRaises(ValueError):
                            allocate_cents(total, weights)
            """,
        ),
    ]
    result = []
    for key, title, issue, before, after, public, independent in specs:
        before, after, public, independent = map(clean, (before, after, public, independent))
        result.append(
            {
                "id": key,
                "title": title,
                "category": "prospective_synthetic",
                "difficulty": "prospective_holdout_v1",
                "issue": issue,
                "files": {
                    "project/__init__.py": "",
                    "project/core.py": before,
                    "tests/test_public.py": public,
                    "README.md": f"# {title}\n\n{issue}\n",
                },
                "heldout": independent,
                "replay_edits": [{"path": "project/core.py", "old": before, "new": after}],
                "provenance": {
                    "origin": "self_authored_synthetic",
                    "evaluation_split": "prospective_holdout_v1",
                    "first_model_exposure": "after frozen protocol admission only",
                    "pretraining_contamination": "unknown",
                    "independent_human_review": False,
                    "requires_docker": True,
                    "public_tests_sha256": sha256(public.encode()),
                    "independent_tests_sha256": sha256(independent.encode()),
                    "reference_source_sha256": sha256(after.encode()),
                },
            }
        )
    return result


if __name__ == "__main__":
    output = Path(__file__).resolve().parents[1] / "src/repofix/fixtures/holdout.json"
    with output.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(build(), handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"tasks": 3, "output": str(output), "model_calls": 0}))
