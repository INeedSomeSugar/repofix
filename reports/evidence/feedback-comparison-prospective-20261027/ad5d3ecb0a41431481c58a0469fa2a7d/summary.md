# RepoFix ad5d3ecb0a41431481c58a0469fa2a7d

- 任务：holdout_inventory_batch
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 反馈协议：layered_v1
- 停止原因：正常结束或预算/异常状态
- 原始测试通过的源码检查点：c7aeb06bfdbe81e389165d569c56916c
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：24.047 秒
- 已知 token：20586
- 补丁 SHA-256：6c942404d45dcda81c8bb845df9d0fad1b4f09272728642e264d9ab1ae829115
- 任务 SHA-256：be78a0365e5a842a0d0ebd8b2c244cdca05087b9a27adb9ba2f6668f00b13622

修改摘要（project/core.py 的 apply_batch）：

- 不再原地修改输入：先校验并复制 stock、versions 到新字典，所有变更只作用于副本，因此成功或中途失败都不会污染输入字典或 changes 中的对象；空变更也返回副本。
- 校验：stock/versions 必须为字典且值为非负整数；changes 必须可迭代，每项须为字典且含 sku/delta/expected_version；delta 须为整数（拒绝 bool），expected_version 须为非负整数（拒绝 bool），否则抛 ValueError。
- 未知 sku 抛 KeyError；版本不匹配或变更后库存为负抛 ValueError；每项成功后版本加 1，同 SKU 后续操作基于递增后的版本检查（delta 为 0 也递增版本）。
- 返回 (new_stock, new_versions) 两个新字典。

新增回归测试 tests/test_agent_batch.py（8 个用例：顺序版本检查、过期版本、未知 SKU、bool 拒绝、负 expected_version、空变更返回副本、delta=0 递增版本、缺键）。

实际执行的公开测试：冻结公开测试 2 个全部通过（test_success_does_not_mutate、test_failure_is_atomic）；自建测试 8 个全部通过。独立评分测试未暴露，未作声明。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
