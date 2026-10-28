# RepoFix 2bc3b974cdc248789a7bc6b8bb3d2192

- 任务：holdout_cursor_page
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 反馈协议：legacy_all
- 停止原因：正常结束或预算/异常状态
- 原始测试通过的源码检查点：无
- 状态：verified
- 模型轮数：9
- 工具次数：10
- 耗时：26.25 秒
- 已知 token：33302
- 补丁 SHA-256：cb604f097fc90e4b10c714a7f3b552f8de5cd6d592f6f371aa622d6ff2d5d83e
- 任务 SHA-256：0c5a2e91e21346d63e556f05b2029231595bcc3236f5ddeb58aef90df4cc5746

修改摘要（project/core.py 的 page）：

- 校验 limit：必须是 int 且非 bool，范围 1–100，否则抛 ValueError。
- 校验并规范化 after：None 或二元素序列（sequence 为 int 非 bool，event_id 为 str），否则 ValueError。
- 不再原地排序输入：遍历可迭代 events，按 (sequence, event_id) 复合键过滤出严格大于游标的记录，再排序后取前 limit 条。
- 返回浅拷贝（dict(row)），不修改输入列表或事件。
- next_cursor 仅当还有后续记录时为本页末条的 [sequence, event_id]，否则 None；空输入或游标之后无记录返回空 items 与 None。

新增回归测试 tests/test_agent_page.py（同序号排序与游标、游标不对应已有事件、空输入/越界游标、非法 limit、不修改输入且返回浅拷贝、可迭代输入）。

实际执行的公开测试：共 8 个测试全部通过（test_public 的 test_invalid_limit、test_same_sequence_and_terminal_cursor，以及新增的 6 个测试）。独立评分测试未运行，不作成功声明。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
