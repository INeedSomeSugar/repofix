# RepoFix 0cfbba22f3054179a8832060e5b811f2

- 任务：holdout_inventory_batch
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 反馈协议：legacy_all
- 停止原因：正常结束或预算/异常状态
- 原始测试通过的源码检查点：无
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：19.938 秒
- 已知 token：18382
- 补丁 SHA-256：3beda77db490ce87e56849c6dd9045377e95038343a6ff00dce92b5e0da5df5f
- 任务 SHA-256：be78a0365e5a842a0d0ebd8b2c244cdca05087b9a27adb9ba2f6668f00b13622

已修复 `project/core.py` 中的 `apply_batch`：

- 先校验并复制 `stock`、`versions`（非负整数，拒绝 bool），所有变更都在副本上进行，因此成功或失败都不会修改输入字典，返回的也是新对象（空变更同样返回副本）。
- 按顺序应用变更：每项校验 `sku`/`delta`/`expected_version` 存在且类型正确（`delta` 为整数含 0，`expected_version` 为非负整数，均拒绝 bool），未知 SKU 抛 `KeyError`，版本不匹配或库存变负抛 `ValueError`；同 SKU 后续操作基于前一次递增后的版本检查，成功后版本加 1。
- 失败时直接抛出异常，不返回部分结果，输入保持原样（原子性）。
- 不修改 `changes` 中的对象。

新增回归测试 `tests/test_agent_batch.py`（顺序版本检查、陈旧版本、bool 拒绝、未知 SKU、空变更返回副本、changes 不被修改）。

实际执行的公开测试结果：共 8 个测试全部通过（含原有 2 个公开测试与新增 6 个测试），0 失败 0 错误。独立评分测试未执行，不作结论。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
