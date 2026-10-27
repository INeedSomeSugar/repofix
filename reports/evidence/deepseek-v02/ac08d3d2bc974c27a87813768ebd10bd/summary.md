# RepoFix ac08d3d2bc974c27a87813768ebd10bd

- 任务：rolling_average
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：11.485 秒
- 已知 token：15480
- 补丁 SHA-256：efd19b161e8a28e62d577be358653d750eee645cf5fd735fa95c47e07fe31161
- 任务 SHA-256：ae839cbb4aa0f89b5faebd2c137d2dc70d280f8d2ce5584de6c58b4633ca9b9e

修改内容（`project/core.py`）：

- 重写 `rolling_average(values, window)`：先校验 `window`，`bool` 或非 `int`（如 `1.0`、`"2"`、`None`）以及 `<= 0` 均抛出 `ValueError`。
- 只输出完整窗口的平均值：先取前 `window` 个元素求和，再用滑动增量（加新元素、减旧元素）逐窗计算，结果长度为 `len(values) - window + 1`。
- 输入为空或 `window > len(values)` 时返回 `[]`。
- 通过 `list(values)` 复制输入，不修改原列表（也支持元组等可迭代序列）。

新增回归测试 `tests/test_agent_rolling.py`，覆盖完整窗口、`window=1`、窗口等于长度、窗口大于长度、空输入、非法 window（含 bool）、输入不被修改、元组输入。

实际执行的公开测试结果：`run_tests` 共运行 10 个测试（2 个公开测试 + 8 个新增测试），全部通过，0 失败 0 错误。独立评分测试未执行，不做结论。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
