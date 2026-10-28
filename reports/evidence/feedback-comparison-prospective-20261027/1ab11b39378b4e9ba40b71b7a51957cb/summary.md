# RepoFix 1ab11b39378b4e9ba40b71b7a51957cb

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
- 耗时：19.625 秒
- 已知 token：18219
- 补丁 SHA-256：2f631e3353c4aa495001d13cad34ec6a2dc91f80319eca72e8dd734b76883817
- 任务 SHA-256：be78a0365e5a842a0d0ebd8b2c244cdca05087b9a27adb9ba2f6668f00b13622

已修复 `project/core.py` 中的 `apply_batch`：

- 先校验 `stock`/`versions` 为字典且值为非负整数，再复制成新字典，所有变更只作用于副本，因此成功或中途失败都不会修改输入。
- 按顺序逐项处理 `changes`：校验每项为字典且含 `sku`/`delta`/`expected_version`；`delta` 必须为整数（拒绝 bool），`expected_version` 必须为非负整数（拒绝 bool）。
- 未知 SKU 抛 `KeyError`；版本不匹配或变更后库存为负抛 `ValueError`；同 SKU 后续操作基于已递增的版本检查。
- 每项成功变更版本加 1；空变更也返回两个新字典副本，且不修改 `changes` 中的对象。

新增回归测试 `tests/test_agent_batch.py`（7 个用例，覆盖顺序版本、过期版本、未知 SKU、bool 拒绝、负版本、空变更返回副本、changes 不被修改）。

实际执行的公开测试结果：共 9 个测试（2 个原有公开测试 + 7 个新增测试）全部通过，0 失败 0 错误。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
