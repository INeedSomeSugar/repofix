# RepoFix 开发任务评测

生成时间：2026-10-26T08:17:18+00:00
代码 SHA-256：45ab05409d23278d99f4fa5c72dce110cb23a8ae6cd467da8c496ad0747f3051

任务为本项目自行编写的合成开发样例。独立评分测试不提供给模型，但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。

| 供应商 | 模型 | 策略 | 尝试 | 通过 | 错误 | 已知 token |
|---|---|---|---:|---:|---:|---:|
| replay | scripted-replay-not-a-model | feedback | 5 | 5 | 0 | N/A |

| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |
|---|---|---|---:|---:|---|
| csv_records | feedback | verified | 6 | 6 | 94840ba3ca8140f6beee8772121eb1ad |
| rolling_average | feedback | verified | 6 | 6 | a0a4451899f64e9f8c98afe8ab019a88 |
| merge_intervals | feedback | verified | 6 | 8 | 77ea8d50e13149baa08774860e235659 |
| ttl_cache | feedback | verified | 6 | 6 | 0a01868aefb047888117013701b2e8c9 |
| top_words | feedback | verified | 6 | 6 | 157251a1d2374cc296db4128eb79e085 |

评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。
token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。
