# RepoFix 7bccfcb021b3493eb18a5867bc9de479

- 任务：ttl_cache
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：11.391 秒
- 已知 token：15251
- 补丁 SHA-256：316b540a31e9974392ba2362c4f052b9c0b09063a7cc55ae51c7939695fb8814
- 任务 SHA-256：49336883f654a755a2c458957bbf7237b21fe9c3fd8a009ac7a80a5a4ce5f20a

修改内容（project/core.py）：

- `set`：`ttl < 0` 时抛出 `ValueError`；过期时间仍为调用方提供的 `now + ttl`（不读取系统时间）。
- `get`：过期判定改为 `now >= 设置时间 + ttl`（边界即过期），过期时删除条目并返回 `default`。
- 未过期时直接返回存储值，不再用 `value or default`，因此 `0`、`False`、`""`、`None` 均原样返回。
- 重新 `set` 直接覆盖旧值与过期时间（字典赋值语义）。

新增回归测试 tests/test_agent_ttl.py，覆盖假值原样返回、边界过期、ttl=0 立即过期、负 ttl 抛错、重新 set 覆盖、缺失键默认值。

实际执行的公开测试结果：共 8 个测试（2 个原有公开测试 + 6 个新增测试）全部通过，0 失败 0 错误。独立评分测试未执行，不做结论。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
