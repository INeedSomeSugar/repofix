# RepoFix c90d64b785604c1e8aa37206c99c04d1

- 任务：top_words
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：10.359 秒
- 已知 token：13812
- 补丁 SHA-256：4c959e11a733a2b5fac97a46e33b49b38b821511a5e56fc52b477e9666eeca3b
- 任务 SHA-256：d6fd786a67353abc9da1b2251a2e6ca4d2ce36d14c7bcd9df1193217a778f929

修改内容（project/core.py）：

- 用 `re.findall(r"[A-Za-z]+", text)` 提取连续 ASCII 字母作为词，非字母字符（数字、标点、非 ASCII 字母）作为分隔符，并统一 `lower()` 忽略大小写。
- 排序键改为 `(-count, word)`，实现次数降序、同频按字典序升序。
- 参数校验：`k` 为 bool、非 int（如 float/str/None）或负数时抛 `ValueError`；`k == 0` 或无词时返回 `[]`；`k` 超过不同词数时返回全部。

新增回归测试 tests/test_agent_top_words.py，覆盖大小写与非 ASCII 过滤、同频字典序、k=0/无词、k 超长、非法 k。

实际执行的公开测试：运行全部测试共 7 个（2 个原有公开测试 + 5 个新增测试），全部通过（failures=0, errors=0）。独立评分测试未运行，不作结论。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
