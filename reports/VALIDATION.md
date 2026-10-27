# v0.1.0 本地交付验证

日期：2026-10-26（Asia/Shanghai）。

| 检查 | 实际结果 |
| --- | --- |
| 工程测试 | 47 passed，包含真实 Python 子进程、HTTP API、失败反馈、恢复、超时和评分标记伪造测试 |
| Ruff | src / tests / scripts 检查通过 |
| JavaScript | `node --check src/repofix/static/app.js` 通过 |
| 依赖 | `uv pip check`：25 个已安装包兼容 |
| 包构建 | 实际生成 `work/dist/repofix_agent-0.1.0-py3-none-any.whl`，包含静态资源与样例数据 |
| 凭据 | 检查非空配置后经用户明确选择，复用进程环境的 DeepSeek Key；没有写入密钥文件 |
| 密钥扫描 | 当时 102 个可分享文件中，当前 DeepSeek/OpenAI 凭据原值匹配为 0 |
| 模型连接 | `/models` 成功，选择实际存在的 `deepseek-flash` |
| 真实模型 | 2 个开发任务 × 2 种策略，4 次运行均通过对应公开与独立测试 |
| 证据包 | 54 个文件与原评测 JSON 的 SHA-256 校验通过 |
| 浏览器 | 已实际点击启动回放并观察到“失败 → 通过”、独立测试通过、轨迹与补丁 |

真实模型原始数据见 `deepseek-development-v01.json`，对应代码指纹为该报告生成时的 Python 源码快照。后续执行器增加可信结果文件通道，工程测试已重新运行；历史模型记录保留原始字节，不改写为新代码的运行结果。

工程测试有一条 Starlette TestClient 使用 httpx 的弃用提示；未影响本轮实际测试。当前仅是本地演示和开发验证，没有生产部署、容器隔离或外部公开基准成绩。
