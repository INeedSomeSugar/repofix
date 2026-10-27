# RepoFix 开发任务评测

生成时间：2026-10-27T07:31:08+00:00
代码 SHA-256：83cea5f2c62e33ec61186fa3b2784684a5bb141a4afb26731ce7a3bedbd57507

任务为本项目自行编写的合成开发样例。独立评分测试不提供给模型，但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。

| 供应商 | 模型 | 策略 | 尝试 | 通过 | 错误 | 已知 token |
|---|---|---|---:|---:|---:|---:|
| replay | scripted-replay-not-a-model | feedback | 3 | 3 | 0 | N/A |

| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |
|---|---|---|---:|---:|---|
| upstream_value_chain | feedback | verified | 6 | 6 | 78039d960d554bdba7b82dffa59dc099 |
| upstream_split_empty | feedback | verified | 6 | 6 | ef9097944107463b811848e3495e7ef5 |
| upstream_custom_exception | feedback | verified | 6 | 6 | 010126e094ae4671a718c77f3a6fb792 |

评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。
token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。
