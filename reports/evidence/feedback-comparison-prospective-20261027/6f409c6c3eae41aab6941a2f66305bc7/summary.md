# RepoFix 6f409c6c3eae41aab6941a2f66305bc7

- 任务：holdout_inventory_batch
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 反馈协议：layered_v1
- 停止原因：正常结束或预算/异常状态
- 原始测试通过的源码检查点：a16405e6d790b40ec54fc56dd5d013a2
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：22.39 秒
- 已知 token：19529
- 补丁 SHA-256：955a0583f7f7b425ae0ca29b09e961abadbfed96d9fb468524d7283d5ff48c45
- 任务 SHA-256：be78a0365e5a842a0d0ebd8b2c244cdca05087b9a27adb9ba2f6668f00b13622

修改摘要（project/core.py 的 apply_batch）：

- 先在 `dict(stock)`、`dict(versions)` 的副本上操作，成功或中途失败都不会修改输入字典，也不修改 changes 中的对象；空变更同样返回两个新字典对象。
- 按顺序逐项处理：先校验 change 为字典且含 sku/delta/expected_version（缺失字段抛 ValueError），delta 必须为 int 且非 bool，expected_version 必须为非负 int 且非 bool，否则抛 ValueError。
- 未知 sku 抛 KeyError；版本不匹配抛 ValueError；变更后库存为负抛 ValueError。
- 版本检查基于副本中已递增的版本，因此同 SKU 的后续操作必须使用前一次递增后的版本；每项成功后版本加 1。
- 返回 `(new_stock, new_versions)`。

新增回归测试 tests/test_agent_batch.py，覆盖顺序版本递增、过期版本、未知 SKU、bool 拒绝、负 expected_version、空变更返回副本、失败不修改输入。

实际执行的公开测试：冻结公开测试 2 项全部通过（test_success_does_not_mutate、test_failure_is_atomic）；自建测试 7 项全部通过。独立评分测试未暴露，未作成功声明。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
