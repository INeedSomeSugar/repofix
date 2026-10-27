# RepoFix 开发任务评测

生成时间：2026-10-26T08:03:29+00:00
代码 SHA-256：1362bac6d7c1cc939279aa0f2114e829e1f658c9f8f49de409bd53f1ae19fe14

任务为本项目自行编写的合成开发样例。独立评分测试不提供给模型，但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。

| 供应商 | 模型 | 策略 | 尝试 | 通过 | 错误 | 已知 token |
|---|---|---|---:|---:|---:|---:|
| deepseek | deepseek-flash | feedback | 2 | 2 | 0 | 32830 |
| deepseek | deepseek-flash | single_patch | 2 | 2 | 0 | 11676 |

| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |
|---|---|---|---:|---:|---|
| csv_records | feedback | verified | 6 | 7 | 388a9f0f4f6e44a09800df788707a77a |
| csv_records | single_patch | verified | 3 | 5 | cf9a23f1702144d5a6feb81cdb70ac7f |
| merge_intervals | feedback | verified | 6 | 9 | 0b4a1f4d112b4066b96778b85d4d6eb1 |
| merge_intervals | single_patch | verified | 3 | 7 | 54cae1ad01b64950ae4bebd1a414e2f0 |

评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。
token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。
