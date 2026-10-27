# RepoFix 开发任务评测

生成时间：2026-10-27T07:38:02+00:00
代码 SHA-256：bd3fdfb6f9fbf2182c5d9a5ccf74be449bac841e7c0e40a0024e074f3fcdf859

任务为本项目自行编写的合成开发样例。独立评分测试不提供给模型，但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。

| 供应商 | 模型 | 策略 | 尝试 | 通过 | 错误 | 已知 token |
|---|---|---|---:|---:|---:|---:|
| replay | scripted-replay-not-a-model | feedback | 3 | 3 | 0 | N/A |

| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |
|---|---|---|---:|---:|---|
| upstream_value_chain | feedback | verified | 6 | 6 | 98b7dfb6c09d4b769bb528e4b721e55e |
| upstream_split_empty | feedback | verified | 6 | 6 | 7d270950685b4d139a831cd2664fb213 |
| upstream_custom_exception | feedback | verified | 6 | 6 | 73edbdec857a4e63b6c37dc05746a81d |

评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。
token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。
