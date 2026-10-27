# RepoFix 46cc60db22e64bcc922ef0ffc4cb84a3

- 任务：csv_records
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：12.766 秒
- 已知 token：16045
- 补丁 SHA-256：9f760c148a54da655ce8d5d1a1aa691846cab07921e09c29876c52caee170fea
- 任务 SHA-256：bc5e721925cee35ade95715b2fb3c5889733809d4ab1c3493518e87f4c4a226b

修改内容（project/core.py）：

- 改用 `csv.reader` + `io.StringIO(text, newline="")` 解析，支持标准 CSV 引号、引号内逗号以及引号内换行；不再用 `split(",")`。
- 首个非空行作为表头；空行与所有字段均为空白的行被跳过（包括表头之前的空行）。
- 每个字段首尾去空白（表头与数据字段都处理）。
- 空输入、纯空白输入、只有表头时返回 `[]`。
- 非空数据行字段数与表头不一致时抛出 `ValueError`。
- 不再对输入做 `strip()`/`splitlines()` 改写，输入字符串保持不变。

新增回归测试 tests/test_agent_csv.py，覆盖空输入/仅表头、表头前空行、空白行跳过、引号与引号内逗号、引号内换行、字段去空白、字段数不一致抛错、输入不被修改。

实际执行的公开测试：共 10 个测试全部通过（含原有 test_public 的 test_basic、test_blank_rows 以及新增的 8 个测试），0 失败 0 错误。独立评分测试未执行，不作结论。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
