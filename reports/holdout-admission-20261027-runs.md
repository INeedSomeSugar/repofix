# RepoFix 开发任务评测

生成时间：2026-10-27T13:49:19+00:00
代码 SHA-256：88d6470f0e65c5a16d268cbcbd1ca5b8edbc29c90b4fb1086c5fe6963956ada4

任务类型：prospective_synthetic_holdout_v1。独立评分测试不提供给模型，但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。

| 供应商 | 模型 | 策略 | 反馈协议 | 尝试 | 通过 | 错误 | 已知 token |
|---|---|---|---|---:|---:|---:|---:|
| replay | scripted-replay-not-a-model | feedback | layered_v1 | 3 | 3 | 0 | N/A |

| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |
|---|---|---|---:|---:|---|
| holdout_cursor_page | feedback | verified | 6 | 6 | 82f820e1899f431fbdfce1d83ea073ef |
| holdout_inventory_batch | feedback | verified | 6 | 6 | 7adba888874142058e50c7ef1d0d5a77 |
| holdout_money_allocation | feedback | verified | 6 | 6 | 66921e3d318644f48b169ca56a8a19ee |

评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。
token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。
