# RepoFix 开发任务评测

生成时间：2026-10-27T13:59:01+00:00
代码 SHA-256：88d6470f0e65c5a16d268cbcbd1ca5b8edbc29c90b4fb1086c5fe6963956ada4

任务类型：prospective_synthetic_holdout_v1。独立评分测试不提供给模型，但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。

| 供应商 | 模型 | 策略 | 反馈协议 | 尝试 | 通过 | 错误 | 已知 token |
|---|---|---|---|---:|---:|---:|---:|
| deepseek | deepseek-flash | feedback | layered_v1 | 6 | 6 | 0 | 205800 |
| deepseek | deepseek-flash | feedback | legacy_all | 6 | 6 | 0 | 137080 |
| deepseek | deepseek-flash | single_patch | legacy_all | 6 | 6 | 0 | 36410 |

| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |
|---|---|---|---:|---:|---|
| holdout_cursor_page | single_patch | verified | 3 | 5 | 08d28e62d29f4310b5e0760bead11439 |
| holdout_cursor_page | feedback | verified | 9 | 10 | 2bc3b974cdc248789a7bc6b8bb3d2192 |
| holdout_cursor_page | feedback | verified | 11 | 12 | 316ae648abd94836832dac967f164624 |
| holdout_inventory_batch | feedback | verified | 6 | 7 | 0cfbba22f3054179a8832060e5b811f2 |
| holdout_inventory_batch | feedback | verified | 6 | 7 | 6f409c6c3eae41aab6941a2f66305bc7 |
| holdout_inventory_batch | single_patch | verified | 3 | 5 | ea67640868a348d291ef8053c65a71a5 |
| holdout_money_allocation | feedback | verified | 11 | 13 | 0f6cff1b3f804e2d839dfd9093d09a1d |
| holdout_money_allocation | single_patch | verified | 3 | 5 | e396ede671fc496b80f04681509012b3 |
| holdout_money_allocation | feedback | verified | 6 | 7 | c1e520c9b95e4f56960107efba392604 |
| holdout_cursor_page | single_patch | verified | 3 | 5 | 7f90f56e650a4323b0d1567e8b95711d |
| holdout_cursor_page | feedback | verified | 6 | 7 | e8f865dec15d40618ca3b43b0f6174ec |
| holdout_cursor_page | feedback | verified | 6 | 7 | e37c5fb41efb486294ae18091df73c11 |
| holdout_inventory_batch | feedback | verified | 6 | 7 | 1ab11b39378b4e9ba40b71b7a51957cb |
| holdout_inventory_batch | single_patch | verified | 3 | 6 | 8e76946f8e6c4279add15aa8fb00349b |
| holdout_inventory_batch | feedback | verified | 6 | 7 | ad5d3ecb0a41431481c58a0469fa2a7d |
| holdout_money_allocation | feedback | verified | 6 | 7 | 9bcfe756194545659d831502ec9ea047 |
| holdout_money_allocation | feedback | verified | 9 | 10 | 6f649273e45e47f99ed829a594d4a732 |
| holdout_money_allocation | single_patch | verified | 3 | 5 | 874153dadb264adeb2b62661d0d6624d |

评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。
token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。
