# RepoFix 开发任务评测

生成时间：2026-10-26T12:24:12+00:00
代码 SHA-256：197ccd6b976301b441697536f52dd5111ccd7b46eac508824e469c9f0f2ee50f

任务为本项目自行编写的合成开发样例。独立评分测试不提供给模型，但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。

| 供应商 | 模型 | 策略 | 尝试 | 通过 | 错误 | 已知 token |
|---|---|---|---:|---:|---:|---:|
| deepseek | deepseek-flash | feedback | 10 | 9 | 0 | 196127 |
| deepseek | deepseek-flash | single_patch | 10 | 10 | 0 | 57676 |

| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |
|---|---|---|---:|---:|---|
| csv_records | feedback | verified | 6 | 7 | 8cd8c2f75ebe4c48bda408c1ce72be89 |
| csv_records | single_patch | verified | 3 | 5 | 6d911809958c4395a10231d56c1de1ad |
| rolling_average | single_patch | verified | 3 | 5 | 6ca9242e14a8441082f9b2fbd1709535 |
| rolling_average | feedback | verified | 6 | 7 | ac08d3d2bc974c27a87813768ebd10bd |
| merge_intervals | feedback | budget_exhausted | 12 | 15 | 6d90ad40367c45b7a9a2e555bf521bca |
| merge_intervals | single_patch | verified | 3 | 7 | 5d4670ad81114281a9fabcc15a7ad815 |
| ttl_cache | single_patch | verified | 3 | 6 | 520e63940dcd4121989860dabd617924 |
| ttl_cache | feedback | verified | 5 | 7 | 89a4b1bd94d343018834c0c9e91e5676 |
| top_words | feedback | verified | 6 | 7 | c90d64b785604c1e8aa37206c99c04d1 |
| top_words | single_patch | verified | 3 | 6 | 5eb5e1c171de4d44858b5c61e121992b |
| csv_records | single_patch | verified | 3 | 5 | 6c756a4b80304f5dafe1453c64284adb |
| csv_records | feedback | verified | 6 | 7 | 46cc60db22e64bcc922ef0ffc4cb84a3 |
| rolling_average | feedback | verified | 6 | 7 | 3e623c7e404146cd8fe2ee8d60e00134 |
| rolling_average | single_patch | verified | 3 | 5 | c5486fc533e243ebbd52791cf9766e3b |
| merge_intervals | single_patch | verified | 3 | 7 | eb807d7c9af54616b581e79ca864ef8a |
| merge_intervals | feedback | verified | 6 | 9 | f76be2542bff49149ef982bddadb3eb6 |
| ttl_cache | feedback | verified | 6 | 7 | 7bccfcb021b3493eb18a5867bc9de479 |
| ttl_cache | single_patch | verified | 3 | 6 | 3c9c4f1d178740e7a14a32af5350f9f8 |
| top_words | single_patch | verified | 3 | 5 | ecb003b9d6674232b5af91e5a42c6775 |
| top_words | feedback | verified | 9 | 10 | 586c4a64790046c6a56f40511af32f32 |

评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。
token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。
