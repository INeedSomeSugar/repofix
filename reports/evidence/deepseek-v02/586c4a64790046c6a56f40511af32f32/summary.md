# RepoFix 586c4a64790046c6a56f40511af32f32

- 任务：top_words
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：9
- 工具次数：10
- 耗时：14.828 秒
- 已知 token：27240
- 补丁 SHA-256：eeb5536a4b03a7fc4ba7e26115cdf51c61526d514397e6ea8101522bff645073
- 任务 SHA-256：d6fd786a67353abc9da1b2251a2e6ca4d2ce36d14c7bcd9df1193217a778f929

修改摘要（中文）：

**实现修复（project/core.py）**
- 用 `re.findall(r"[A-Za-z]+", text)` 提取连续 ASCII 字母作为词，非 ASCII 字母（如 é）与数字、标点均作为分隔符。
- 统一 `lower()` 忽略大小写后计数。
- 排序键改为 `(-count, word)`，实现次数降序、同频按字典序升序。
- 参数校验：`k` 为 bool、非 int（如 float/str/None）或负数时抛 `ValueError`；`k == 0` 直接返回 `[]`；无词时返回 `[]`；`k` 超过不同词数时返回全部。

**新增回归测试（tests/test_agent_top_words.py）**
覆盖大小写合并、非 ASCII 分隔、同频字典序、k=0/无词、k 超长、非法 k（-1、True、False、1.0、"2"、None）。

**实际执行的公开测试结果**
运行全部测试共 8 个：`test_public.PublicTests.test_counts`、`test_public.PublicTests.test_tie` 以及新增 6 个测试全部通过（Ran 8 tests, OK）。独立评分测试未运行，不作成功声明。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
