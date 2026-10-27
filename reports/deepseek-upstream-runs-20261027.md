# RepoFix 开发任务评测

生成时间：2026-10-27T07:37:19+00:00
代码 SHA-256：bd3fdfb6f9fbf2182c5d9a5ccf74be449bac841e7c0e40a0024e074f3fcdf859

任务为本项目自行编写的合成开发样例。独立评分测试不提供给模型，但不代表外部专家或公开基准验证。小样本仅展示当前执行情况。

| 供应商 | 模型 | 策略 | 尝试 | 通过 | 错误 | 已知 token |
|---|---|---|---:|---:|---:|---:|
| deepseek | deepseek-flash | feedback | 3 | 3 | 0 | 64815 |
| deepseek | deepseek-flash | single_patch | 3 | 3 | 0 | 19779 |

| 任务 | 策略 | 状态 | 模型轮数 | 工具次数 | run_id |
|---|---|---|---:|---:|---|
| upstream_value_chain | feedback | verified | 6 | 8 | b41fb232652446548b707ae7433a188a |
| upstream_value_chain | single_patch | verified | 3 | 6 | 965f6b289ab14f80a1998f676c345080 |
| upstream_split_empty | single_patch | verified | 3 | 6 | a626cca05a9a488da0c3614674a96583 |
| upstream_split_empty | feedback | verified | 7 | 8 | 6fe388ead937482c9f7a78ccb2512046 |
| upstream_custom_exception | feedback | verified | 7 | 8 | 13f428463f75487fa662d4efc1fa1268 |
| upstream_custom_exception | single_patch | verified | 3 | 5 | efb446cb276543f7ba7e7911d2821367 |

评分要求：原始可见测试失败，源码确实改变，最终可见测试与独立测试全部通过。
token 为接口返回的实际用量，缺失时不估算。回放不产生真实模型修复率。
