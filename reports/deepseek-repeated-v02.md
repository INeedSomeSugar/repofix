# RepoFix 重复开发试验

Repeated trusted synthetic development trials only; not external benchmark or general repair accuracy. Identical caps do not imply equal actual compute.

协议SHA256：bb5362bd623c7f97dbd4174daeddfe826907ee5e7690951fb1b3bfdbc7ba5dcc
模型：deepseek-flash；每任务重复：2

| 策略 | 尝试 | 通过 | 已知token | 完整token统计 | 耗时中位数/秒 |
|---|---:|---:|---:|---|---:|
| feedback | 10 | 9 | 196127 | True | 11.812999999999999 |
| single_patch | 10 | 10 | 57676 | True | 5.6015 |

## 全部逐任务配对结果

- csv_records: {"both_verified": 2}
- rolling_average: {"both_verified": 2}
- merge_intervals: {"single_patch_only": 1, "both_verified": 1}
- ttl_cache: {"both_verified": 2}
- top_words: {"both_verified": 2}

## 原始运行

- csv_records / repeat=1 / feedback: verified / 8cd8c2f75ebe4c48bda408c1ce72be89
- csv_records / repeat=1 / single_patch: verified / 6d911809958c4395a10231d56c1de1ad
- rolling_average / repeat=1 / single_patch: verified / 6ca9242e14a8441082f9b2fbd1709535
- rolling_average / repeat=1 / feedback: verified / ac08d3d2bc974c27a87813768ebd10bd
- merge_intervals / repeat=1 / feedback: budget_exhausted / 6d90ad40367c45b7a9a2e555bf521bca
- merge_intervals / repeat=1 / single_patch: verified / 5d4670ad81114281a9fabcc15a7ad815
- ttl_cache / repeat=1 / single_patch: verified / 520e63940dcd4121989860dabd617924
- ttl_cache / repeat=1 / feedback: verified / 89a4b1bd94d343018834c0c9e91e5676
- top_words / repeat=1 / feedback: verified / c90d64b785604c1e8aa37206c99c04d1
- top_words / repeat=1 / single_patch: verified / 5eb5e1c171de4d44858b5c61e121992b
- csv_records / repeat=2 / single_patch: verified / 6c756a4b80304f5dafe1453c64284adb
- csv_records / repeat=2 / feedback: verified / 46cc60db22e64bcc922ef0ffc4cb84a3
- rolling_average / repeat=2 / feedback: verified / 3e623c7e404146cd8fe2ee8d60e00134
- rolling_average / repeat=2 / single_patch: verified / c5486fc533e243ebbd52791cf9766e3b
- merge_intervals / repeat=2 / single_patch: verified / eb807d7c9af54616b581e79ca864ef8a
- merge_intervals / repeat=2 / feedback: verified / f76be2542bff49149ef982bddadb3eb6
- ttl_cache / repeat=2 / feedback: verified / 7bccfcb021b3493eb18a5867bc9de479
- ttl_cache / repeat=2 / single_patch: verified / 3c9c4f1d178740e7a14a32af5350f9f8
- top_words / repeat=2 / single_patch: verified / ecb003b9d6674232b5af91e5a42c6775
- top_words / repeat=2 / feedback: verified / 586c4a64790046c6a56f40511af32f32
