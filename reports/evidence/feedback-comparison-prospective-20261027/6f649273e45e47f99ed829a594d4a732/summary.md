# RepoFix 6f649273e45e47f99ed829a594d4a732

- 任务：holdout_money_allocation
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 反馈协议：legacy_all
- 停止原因：正常结束或预算/异常状态
- 原始测试通过的源码检查点：无
- 状态：verified
- 模型轮数：9
- 工具次数：10
- 耗时：28.812 秒
- 已知 token：33770
- 补丁 SHA-256：003c503510471687c5ca88ce41fc7e572f0df9f411ac1b02dbb5bf45092d6d57
- 任务 SHA-256：b7325425a9e67ce00fcc8ae91667f3ab8cff80fc7f5ed51cb4d655fb0b99dd33

修改摘要（中文）：

- `project/core.py` 的 `allocate_cents` 已重写为纯整数实现的最大余数法：
  - 校验 `total` 必须是 `int` 且非 `bool`，否则 `ValueError`。
  - `weights` 接受任意可迭代对象（拒绝 `str`/`bytes`/`bytearray` 与不可迭代对象），逐项校验为非负 `int` 且非 `bool`；不修改输入（先转成列表副本）。
  - 空 `weights`：`total == 0` 返回 `[]`，否则 `ValueError`；非空时权重和必须 `> 0`。
  - 用 `divmod(abs(total) * weight, sum_weights)` 精确计算商与余数，按余数降序、索引升序补足剩余分，最后统一乘符号恢复 `total` 的符号，保证合计等于 `total`，全程无浮点运算。
- 新增回归测试 `tests/test_agent_allocate.py`，覆盖公开示例、正负守恒与符号、并列余数按索引、零权重、可迭代输入与不修改输入、空权重、各类非法类型/负权重/权重和为 0、超大整数精确性。

实际执行的公开测试结果：`run_tests` 共运行 10 个测试（2 个公开测试 + 8 个新增测试），全部通过（failures 0, errors 0）。独立评分测试未运行，未作任何成功声明。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
