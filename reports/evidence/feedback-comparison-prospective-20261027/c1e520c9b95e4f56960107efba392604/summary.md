# RepoFix c1e520c9b95e4f56960107efba392604

- 任务：holdout_money_allocation
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 反馈协议：legacy_all
- 停止原因：正常结束或预算/异常状态
- 原始测试通过的源码检查点：无
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：19.593 秒
- 已知 token：16888
- 补丁 SHA-256：fe177b220b863971330af429b953cba71ebf14858ec6d3cfdbdf44f6d0e9adeb
- 任务 SHA-256：b7325425a9e67ce00fcc8ae91667f3ab8cff80fc7f5ed51cb4d655fb0b99dd33

修改内容（project/core.py）：

- 重写 `allocate_cents`，改为纯整数运算的最大余数法：以 `abs(total)` 计算 `magnitude * weight // denominator` 作为基础份额，余数 `magnitude * weight % denominator` 按“余数降序、原始索引升序”排序后依次补 1 分，最后统一乘以 `total` 的符号，保证合计等于 `total`，全程无浮点。
- 参数校验：`total` 必须是非 bool 的 `int`；`weights` 必须是非字符串可迭代对象（支持生成器，内部转 list，不修改输入），每个权重必须是非 bool 的非负整数；空权重仅 `total == 0` 返回 `[]`，否则 `ValueError`；非空权重总和须大于 0，否则 `ValueError`。

新增回归测试 tests/test_agent_allocate.py，覆盖公开示例、正负金额守恒、零权重、余数并列按索引、空权重、非法类型/负权重、输入不被修改、生成器权重。

实际执行的公开测试结果：共运行 10 个测试（2 个原有公开测试 + 8 个新增测试），全部通过（failures 0, errors 0）。独立评分测试未执行，不作结论。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
