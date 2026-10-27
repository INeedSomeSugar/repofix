# RepoFix 6fe388ead937482c9f7a78ccb2512046

- 任务：upstream_split_empty
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：7
- 工具次数：8
- 耗时：20.968 秒
- 已知 token：25796
- 补丁 SHA-256：0906f6f9bf6beadcee9e166bb233b1e8fe5f874ad35cadf9f3273a313f6d59a2
- 任务 SHA-256：0f0a8e318c71871484bc3b63183af9d09c42ab3b7b413abac434134df78f993d

修改说明（中文）：

**问题**：`split_before`、`split_after`、`split_when` 在 `maxsplit == 0` 时无条件 `yield list(iterable)`，导致空输入产生 `[[]]` 而非 `[]`。

**修复**（`project/core.py`）：三个函数的 `maxsplit == 0` 分支改为先物化输入，仅当结果非空时才产出一个包含全部内容的分组；空输入直接返回零个分组。其余拆分位置、惰性生成器语义、`maxsplit` 递减与提前终止逻辑均未改动。

**新增回归测试**（`tests/test_agent_split_zero.py`）：覆盖空输入/非空输入在 `maxsplit=0` 下的行为、`maxsplit=0` 时仍为惰性生成器（不提前消费输入），以及 `maxsplit=2`、默认 `-1` 下三个函数原有拆分结果不变。

**实际执行的公开测试**：`run_tests` 共运行 6 个测试（2 个公开测试 + 4 个新增测试），全部通过（failures=0, errors=0）。独立评分测试未运行，不作成功声明。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
