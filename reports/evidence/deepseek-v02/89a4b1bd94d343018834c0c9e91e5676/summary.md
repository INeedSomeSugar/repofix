# RepoFix 89a4b1bd94d343018834c0c9e91e5676

- 任务：ttl_cache
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：5
- 工具次数：7
- 耗时：9.344 秒
- 已知 token：12745
- 补丁 SHA-256：9de396edc4c771f233c44dd1c3af18f6ed0d9f25e3db8690d41d8773c5c41cae
- 任务 SHA-256：49336883f654a755a2c458957bbf7237b21fe9c3fd8a009ac7a80a5a4ce5f20a

修改内容（project/core.py）：

- `set`：当 `ttl < 0` 时抛出 `ValueError`；过期时间按调用方提供的 `now + ttl` 计算（不再使用系统时间）。
- `get`：过期判定改为 `now >= 设置时间 + ttl`（边界即过期），过期时删除条目并返回 `default`。
- 未过期时直接返回存储值，不再用 `value or default`，因此 `0`、`False`、`""`、`None` 都原样返回。
- 重新 `set` 同一 key 会覆盖旧值与过期时间（字典赋值天然覆盖）。

新增回归测试 tests/test_agent_ttl.py，覆盖边界过期、假值原样返回、负 ttl 抛错、ttl=0 立即过期、重新 set 覆盖、缺失 key 返回 default。

实际执行的公开测试结果：共 8 个测试（2 个公开 + 6 个新增），全部通过（failures=0, errors=0）。独立评分测试未运行，不作结论。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
