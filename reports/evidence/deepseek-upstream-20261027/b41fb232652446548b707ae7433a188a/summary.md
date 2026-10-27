# RepoFix b41fb232652446548b707ae7433a188a

- 任务：upstream_value_chain
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：6
- 工具次数：8
- 耗时：18.391 秒
- 已知 token：15682
- 补丁 SHA-256：864a54d812933b0361021e36f098aa045d007923b9543b361bb54d2021d34caa
- 任务 SHA-256：1b32948eb8008f06e0518bb81bf81f3f3aee303d13d7ce2388cd92d8344cfbd7

修改说明（中文）：

**问题**：原实现用 `try: yield from value / except TypeError: yield value`，把“迭代过程中抛出的 TypeError”误判为“不可迭代”，从而吞掉错误并把迭代器本身当作标量输出。

**修复**（`project/core.py`）：
- 字符串 `str` 与 `bytes` 仍原样输出（不展开）。
- 先用 `iter(value)` 单独探测可迭代性：只有 `iter()` 本身抛 `TypeError`（即真正不可迭代）才作为标量输出。
- 一旦 `iter()` 成功，改用 `yield from iterator`，此后迭代器内部抛出的任何异常（含 `TypeError`）都向调用者传播，不再被吞掉或输出该迭代器。

**新增回归测试**（`tests/test_agent_value_chain.py`）：覆盖标量/字符串/bytes 原样输出、不可迭代对象作标量、`map` 消费中途 TypeError 传播、自定义迭代器中途 TypeError 传播、嵌套不展平。

**实际执行的公开测试**：`run_tests` 共运行 7 个测试（2 个公开测试 + 5 个新增测试），全部通过（failures=0, errors=0）。独立评分测试未执行，不作成功声明。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
