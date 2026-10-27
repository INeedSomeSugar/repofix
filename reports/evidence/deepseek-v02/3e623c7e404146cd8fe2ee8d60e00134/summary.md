# RepoFix 3e623c7e404146cd8fe2ee8d60e00134

- 任务：rolling_average
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：10.735 秒
- 已知 token：15607
- 补丁 SHA-256：fad64021b1ceeb3e5d60bb0c93c334239a8fb1ff98a5f38ff0f385b6efb04e4e
- 任务 SHA-256：ae839cbb4aa0f89b5faebd2c137d2dc70d280f8d2ce5584de6c58b4633ca9b9e

修改内容（`project/core.py` 中的 `rolling_average`）：

- 只输出完整窗口的平均值：结果长度为 `len(values) - window + 1`，不再包含前缀不完整窗口。
- 参数校验：`window` 必须是正整数且不能是 `bool`（`True`/`False` 也拒绝），否则抛出 `ValueError`；非整数（如 `1.0`、`"2"`、`None`）同样抛出 `ValueError`。
- 输入为空或 `window > len(values)` 时返回 `[]`。
- 先复制输入为列表，不修改原输入；支持列表与元组等可迭代序列。
- 使用滑动和（增量加减）计算，复杂度 O(n)。

新增回归测试 `tests/test_agent_rolling.py`，覆盖完整窗口、window=1、window 等于长度、窗口过大/空输入、非法 window（含 bool）、输入不被修改、元组输入。

实际执行的公开测试结果：共运行 9 个测试（2 个公开测试 + 7 个新增测试），全部通过（failures=0, errors=0）。独立评分测试未执行，不作结论。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
