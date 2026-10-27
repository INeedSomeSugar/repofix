"""Rebuild the original, synthetic development exercises. No downloaded benchmarks."""

import json
from pathlib import Path
from textwrap import dedent


def text(value):
    return dedent(value).lstrip("\n")


def case(case_id, title, category, issue, source, solution, public, heldout, extra=None):
    original = {"project/__init__.py": "", "project/core.py": text(source)}
    original.update(extra or {})
    original["tests/test_public.py"] = text(public)
    original["README.md"] = f"# {title}\n\n{issue}\n"
    return {
        "id": case_id,
        "title": title,
        "category": category,
        "difficulty": "development",
        "issue": issue,
        "files": original,
        "heldout": text(heldout),
        "replay_edits": [{"path": "project/core.py", "old": text(source), "new": text(solution)}],
        "provenance": "Original synthetic development exercise authored for RepoFix; not SWE-bench",
    }


cases = [
    case(
        "csv_records",
        "CSV 空行与引号解析",
        "parsing",
        "修复 project.core.parse_records(text)。首个非空行是表头；跳过空行和仅含空白字段的行；"
        "支持标准 CSV 引号和引号内逗号；字段首尾去空白；空输入和只有表头时返回 []。"
        "非空数据行字段数与表头不一致时抛出 ValueError。保持输入字符串不变。",
        """
        def parse_records(text):
            lines = text.strip().splitlines()
            if not lines:
                return []
            headers = [value.strip() for value in lines[0].split(",")]
            return [dict(zip(headers, [v.strip() for v in line.split(",")]))
                    for line in lines[1:]]
        """,
        """
        import csv
        from io import StringIO


        def parse_records(text):
            rows = ([value.strip() for value in row] for row in csv.reader(StringIO(text)))
            nonempty = (row for row in rows if any(row))
            headers = next(nonempty, None)
            if headers is None:
                return []
            result = []
            for row in nonempty:
                if len(row) != len(headers):
                    raise ValueError("CSV field count does not match header")
                result.append(dict(zip(headers, row)))
            return result
        """,
        """
        import unittest
        from project.core import parse_records


        class PublicTests(unittest.TestCase):
            def test_basic(self):
                self.assertEqual(parse_records("name,age\\nAmy,20"), [{"name": "Amy", "age": "20"}])

            def test_blank_rows(self):
                self.assertEqual(parse_records("name,age\\nAmy,20\\n\\nBob,21"),
                                 [{"name": "Amy", "age": "20"}, {"name": "Bob", "age": "21"}])
        """,
        """
        import unittest
        from project.core import parse_records


        class IndependentTests(unittest.TestCase):
            def test_quoted_comma(self):
                self.assertEqual(parse_records('name,note\\nAmy,"hello, world"'),
                                 [{"name": "Amy", "note": "hello, world"}])

            def test_empty(self):
                self.assertEqual(parse_records(" \\n\\n"), [])
                self.assertEqual(parse_records("name,age"), [])

            def test_whitespace_and_leading_blank(self):
                self.assertEqual(parse_records("\\n name , age \\n , \\n Amy , 20 "),
                                 [{"name": "Amy", "age": "20"}])

            def test_field_count(self):
                with self.assertRaises(ValueError):
                    parse_records("a,b\\n1,2,3")
                with self.assertRaises(ValueError):
                    parse_records("a,b\\n1")
        """,
    ),
    case(
        "rolling_average",
        "滑动平均窗口边界",
        "algorithm",
        "修复 project.core.rolling_average(values, window)。只返回完整窗口的平均值；"
        "例如 [1,2,3,4]、window=2 得到 [1.5,2.5,3.5]。window 必须是正整数且不能是 bool，"
        "否则抛出 ValueError。窗口大于输入长度或输入为空时返回 []，不能修改输入列表。",
        """
        def rolling_average(values, window):
            return [sum(values[max(0, i - window):i + 1]) / window
                    for i in range(len(values))]
        """,
        """
        def rolling_average(values, window):
            if not isinstance(window, int) or isinstance(window, bool) or window <= 0:
                raise ValueError("window must be a positive integer")
            return [sum(values[i:i + window]) / window
                    for i in range(len(values) - window + 1)]
        """,
        """
        import unittest
        from project.core import rolling_average


        class PublicTests(unittest.TestCase):
            def test_full_windows(self):
                self.assertEqual(rolling_average([1, 2, 3, 4], 2), [1.5, 2.5, 3.5])

            def test_window_one(self):
                self.assertEqual(rolling_average([2, 5], 1), [2, 5])
        """,
        """
        import unittest
        from project.core import rolling_average


        class IndependentTests(unittest.TestCase):
            def test_empty_or_large(self):
                self.assertEqual(rolling_average([], 2), [])
                self.assertEqual(rolling_average([1], 2), [])

            def test_invalid_window(self):
                for window in (0, -1, True, 1.5):
                    with self.assertRaises(ValueError):
                        rolling_average([1, 2], window)

            def test_nonmutating(self):
                values = [-3, 1, 5]
                self.assertEqual(rolling_average(values, 3), [1.0])
                self.assertEqual(values, [-3, 1, 5])
        """,
    ),
    case(
        "merge_intervals",
        "跨文件区间合并",
        "multi_file",
        "修复 project.core.merge_intervals(intervals)。输入为 start <= end 的闭区间二元列表。"
        "合并重叠及端点相接的区间，按起点排序返回新列表；不允许修改输入或复用输入的子列表。"
        "空输入返回 []，要检查 project/utils.py 中的重叠判断。",
        """
        from .utils import overlaps


        def merge_intervals(intervals):
            intervals.sort()
            result = []
            for item in intervals:
                if result and overlaps(result[-1], item):
                    result[-1][1] = max(result[-1][1], item[1])
                else:
                    result.append(item)
            return result
        """,
        """
        from .utils import overlaps


        def merge_intervals(intervals):
            ordered = sorted([list(item) for item in intervals])
            result = []
            for item in ordered:
                if result and overlaps(result[-1], item):
                    result[-1][1] = max(result[-1][1], item[1])
                else:
                    result.append(item)
            return result
        """,
        """
        import unittest
        from project.core import merge_intervals


        class PublicTests(unittest.TestCase):
            def test_overlapping(self):
                self.assertEqual(merge_intervals([[1, 4], [2, 5], [8, 9]]), [[1, 5], [8, 9]])

            def test_touching(self):
                self.assertEqual(merge_intervals([[1, 2], [2, 3]]), [[1, 3]])
        """,
        """
        import unittest
        from project.core import merge_intervals


        class IndependentTests(unittest.TestCase):
            def test_input_unchanged(self):
                values = [[4, 6], [1, 5]]
                result = merge_intervals(values)
                self.assertEqual(result, [[1, 6]])
                self.assertEqual(values, [[4, 6], [1, 5]])

            def test_no_alias(self):
                values = [[1, 2]]
                result = merge_intervals(values)
                result[0][1] = 99
                self.assertEqual(values, [[1, 2]])

            def test_empty_and_nested(self):
                self.assertEqual(merge_intervals([]), [])
                self.assertEqual(merge_intervals([[1, 10], [3, 4], [10, 12]]), [[1, 12]])
        """,
        extra={"project/utils.py": "def overlaps(left, right):\n    return right[0] < left[1]\n"},
    ),
    case(
        "ttl_cache",
        "缓存过期与假值",
        "stateful",
        "修复 project.core.TTLCache。set(key,value,ttl,now) 使用调用方提供的时间；ttl<0 抛出"
        " ValueError。get(key,now,default=None) 在 now >= 设置时间+ttl 时过期并返回 default；"
        "未过期的 0、False、空字符串和 None 都必须原样返回。重新 set 应覆盖旧值和过期时间。",
        """
        class TTLCache:
            def __init__(self):
                self._items = {}

            def set(self, key, value, ttl, now):
                self._items[key] = (value, now + ttl)

            def get(self, key, now, default=None):
                if key not in self._items:
                    return default
                value, expires = self._items[key]
                if now > expires:
                    del self._items[key]
                    return default
                return value or default
        """,
        """
        class TTLCache:
            def __init__(self):
                self._items = {}

            def set(self, key, value, ttl, now):
                if ttl < 0:
                    raise ValueError("ttl cannot be negative")
                self._items[key] = (value, now + ttl)

            def get(self, key, now, default=None):
                if key not in self._items:
                    return default
                value, expires = self._items[key]
                if now >= expires:
                    del self._items[key]
                    return default
                return value
        """,
        """
        import unittest
        from project.core import TTLCache


        class PublicTests(unittest.TestCase):
            def test_boundary(self):
                cache = TTLCache()
                cache.set("a", 1, ttl=5, now=10)
                self.assertEqual(cache.get("a", now=14), 1)
                self.assertIsNone(cache.get("a", now=15))

            def test_zero_value(self):
                cache = TTLCache()
                cache.set("a", 0, ttl=5, now=10)
                self.assertEqual(cache.get("a", now=11, default=99), 0)
        """,
        """
        import unittest
        from project.core import TTLCache


        class IndependentTests(unittest.TestCase):
            def test_falsey_values(self):
                cache = TTLCache()
                for value in (False, "", None):
                    cache.set("a", value, ttl=2, now=0)
                    self.assertIs(cache.get("a", now=1, default="missing"), value)

            def test_zero_ttl(self):
                cache = TTLCache()
                cache.set("a", 1, ttl=0, now=0)
                self.assertEqual(cache.get("a", now=0, default=99), 99)

            def test_negative_ttl(self):
                with self.assertRaises(ValueError):
                    TTLCache().set("a", 1, ttl=-1, now=0)

            def test_overwrite(self):
                cache = TTLCache()
                cache.set("a", 1, ttl=1, now=0)
                cache.set("a", 2, ttl=10, now=1)
                self.assertEqual(cache.get("a", now=2), 2)
        """,
    ),
    case(
        "top_words",
        "词频排序与参数校验",
        "text_processing",
        "修复 project.core.top_words(text,k)。将连续 ASCII 英文字母 a-z/A-Z 视为一个词，"
        "忽略大小写，按出现次数降序、同频时按词的字典序升序，返回前 k 个 (word,count) 元组。"
        "k=0 或无词时返回 []。k 为负数、bool 或非整数时抛出 ValueError。",
        """
        def top_words(text, k):
            counts = {}
            for word in text.split():
                counts[word] = counts.get(word, 0) + 1
            return sorted(counts.items(), key=lambda item: item[1], reverse=True)[:k]
        """,
        """
        import re
        from collections import Counter


        def top_words(text, k):
            if not isinstance(k, int) or isinstance(k, bool) or k < 0:
                raise ValueError("k must be a nonnegative integer")
            counts = Counter(re.findall(r"[a-z]+", text.lower()))
            return sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:k]
        """,
        """
        import unittest
        from project.core import top_words


        class PublicTests(unittest.TestCase):
            def test_counts(self):
                self.assertEqual(top_words("cat dog cat", 1), [("cat", 2)])

            def test_tie(self):
                self.assertEqual(top_words("dog cat", 2), [("cat", 1), ("dog", 1)])
        """,
        """
        import unittest
        from project.core import top_words


        class IndependentTests(unittest.TestCase):
            def test_case_and_punctuation(self):
                self.assertEqual(top_words("CAT, cat! Dog; dog cat.", 2), [("cat", 3), ("dog", 2)])

            def test_zero_empty(self):
                self.assertEqual(top_words("a b", 0), [])
                self.assertEqual(top_words("123 !", 10), [])

            def test_invalid_k(self):
                for k in (-1, True, 1.5):
                    with self.assertRaises(ValueError):
                        top_words("a b", k)
        """,
    ),
]

cases[2]["replay_edits"].append(
    {
        "path": "project/utils.py",
        "old": cases[2]["files"]["project/utils.py"],
        "new": "def overlaps(left, right):\n    return right[0] <= left[1]\n",
    }
)

if __name__ == "__main__":
    destination = Path(__file__).resolve().parents[1] / "src/repofix/fixtures/cases.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(cases)} original synthetic exercises to {destination}")
