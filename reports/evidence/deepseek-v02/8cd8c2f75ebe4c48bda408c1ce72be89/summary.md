# RepoFix 8cd8c2f75ebe4c48bda408c1ce72be89

- 任务：csv_records
- 模式：真实 DeepSeek 模型
- 模型：deepseek-flash
- 策略：feedback
- 状态：verified
- 模型轮数：6
- 工具次数：7
- 耗时：12.781 秒
- 已知 token：16128
- 补丁 SHA-256：4a82dc4ab2ce2be3cea60536ac5b0c66d8a0a3fb51ec9e5c84c2914038673d66
- 任务 SHA-256：bc5e721925cee35ade95715b2fb3c5889733809d4ab1c3493518e87f4c4a226b

修改摘要（中文）：

**改动文件：`project/core.py`**
- 用 `csv.reader` + `io.StringIO(text, newline="")` 替代原来的 `split(",")`，从而支持标准 CSV 引号、引号内逗号、转义双引号以及引号内换行。
- 首个非空行作为表头；空行与所有字段均为空白（strip 后为空）的行被跳过（包括表头前的空行）。
- 每个字段首尾去空白（表头与数据行都处理）。
- 空输入、纯空白输入、只有表头时返回 `[]`。
- 非空数据行字段数与表头不一致时抛出 `ValueError`（含实际/期望字段数信息）。
- 不修改输入字符串（只读取，不做原地操作）；非字符串输入抛 `TypeError`。

**新增测试：`tests/test_agent_csv.py`**（8 个用例）：空/仅表头、表头前空行、纯空白行跳过、引号与引号内逗号及转义引号、引号内换行、字段去空白、字段数不一致抛错、输入不被修改。

**实际执行的公开测试结果**：运行全部测试共 10 个，全部通过（`test_public` 的 `test_basic`、`test_blank_rows` 均 ok，新增 8 个用例均 ok），0 失败 0 错误。独立评分测试未运行，不作成功声明。

合成开发样例的评分结果仅用于当前任务，不代表公开基准或生产效果。
