# RepoFix 开发任务评测

生成时间：2026-10-27T08:46:40+00:00
代码 SHA-256：f7081998c6f01898fa15e64f93ff6c53e8610fc1ade0a2fa1430cfe55c5f2f68

任务为本项目自行编写的合成开发样例。独立评分测试不提供给模型，但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。

| 供应商 | 模型 | 策略 | 反馈协议 | 尝试 | 通过 | 错误 | 已知 token |
|---|---|---|---|---:|---:|---:|---:|
| replay | scripted-feedback-validation-not-a-model | feedback | layered_v1 | 3 | 1 | 0 | N/A |

| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |
|---|---|---|---:|---:|---|
| rolling_average | feedback | needs_review | 4 | 3 | 0850137837a74b05b4e94e9e025b8dab |
| rolling_average | feedback | stalled | 3 | 3 | 8d1de1aecf1c4090976f1a09ac2a4f74 |
| rolling_average | feedback | verified | 7 | 6 | cc5fc95476dd43c5a3d2e7a0add46dde |

评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。
token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。
