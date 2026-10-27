# RepoFix 13f428463f75487fa662d4efc1fa1268

- 任务：upstream_custom_exception
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：7
- 工具次数：8
- 耗时：21.468 秒
- 已知 token：23337
- 补丁 SHA-256：d90f3e6c2ae11157182ebc8d35ce08420ca2b91929b4b6802658413d5fcb6a0e
- 任务 SHA-256：bd1d5f13df39bccdb429ed7b4b23516091d57d7534081a8c15e356bdd827363c

修改说明（中文）：

**问题**：`one` 和 `only` 用 `raise too_long or ValueError(msg)` / `raise too_short or ValueError(...)` 判断，导致布尔值为 `False` 的自定义异常被忽略；且即使提供了自定义 `too_long`，也会先构造含 `repr(first)`/`repr(second)` 的默认消息，元素 `repr` 抛错时会覆盖自定义异常。

**修复**（`project/core.py`）：
- 改为显式 `is None` 判断：仅当 `too_long`/`too_short` 为 `None` 时才构造默认消息并抛 `ValueError`，否则直接 `raise too_long` / `raise too_short`，因此布尔值为 `False` 的异常实例也会被抛出。
- 自定义 `too_long` 分支不再构造含元素 `repr` 的默认消息，避免 `repr` 错误覆盖自定义异常。
- 保留行为：单元素返回该元素；`one` 空输入抛 `ValueError`（或自定义 `too_short`）；`only` 空输入返回 `default`。

**新增回归测试** `tests/test_agent_one_only.py`：覆盖 falsy 自定义异常、`repr` 抛错元素 + 自定义 `too_long`、默认消息、单元素/空输入/default 行为。

**实际执行的公开测试**：`run_tests` 共运行 7 个测试（3 个公开测试 + 4 个新增测试），全部通过（failures=0, errors=0）。独立评分测试未运行，不作结论。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
