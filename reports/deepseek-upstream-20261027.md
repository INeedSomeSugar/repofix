# RepoFix 重复开发试验

Fixed trusted development trials only; not external benchmark or general repair accuracy. Identical caps do not imply equal actual compute.

协议SHA256：b4fd065fe4f4ecdbda0d19c7374c12786f1f94eeabacbb74a58cc881cb2248fc
模型：deepseek-flash；每任务重复：1

| 策略 | 尝试 | 通过 | 已知token | 完整token统计 | 耗时中位数/秒 |
|---|---:|---:|---:|---|---:|
| feedback | 3 | 3 | 64815 | True | 20.968 |
| single_patch | 3 | 3 | 19779 | True | 9.969 |

## 全部逐任务配对结果

- upstream_value_chain: {"both_verified": 1}
- upstream_split_empty: {"both_verified": 1}
- upstream_custom_exception: {"both_verified": 1}

## 原始运行

- upstream_value_chain / repeat=1 / feedback: verified / b41fb232652446548b707ae7433a188a
- upstream_value_chain / repeat=1 / single_patch: verified / 965f6b289ab14f80a1998f676c345080
- upstream_split_empty / repeat=1 / single_patch: verified / a626cca05a9a488da0c3614674a96583
- upstream_split_empty / repeat=1 / feedback: verified / 6fe388ead937482c9f7a78ccb2512046
- upstream_custom_exception / repeat=1 / feedback: verified / 13f428463f75487fa662d4efc1fa1268
- upstream_custom_exception / repeat=1 / single_patch: verified / efb446cb276543f7ba7e7911d2821367
