# RepoFix 开发约定

- 首先阅读 README.md、PROJECT_CONTEXT.md 和 docs/ARCHITECTURE.md。
- 独立项目，不修改相邻的 knowledge-rag-lab。
- 密钥仅来自进程环境或本机未跟踪的 .env；禁止输出、存入 trace 或提交密钥。
- replay 是固定脚本回放，仅证明工程链路，不能计入真实模型修复率。
- 内置任务为人工编写的合成开发样例，不是 SWE-bench，也不是独立人工审核基准。
- 模型仅能访问运行目录内的可见仓库；独立评分测试不进入模型上下文。
- public tests、任务说明和已有基线文件必须冻结；仅允许修改 project/*.py 并新增 tests/test_agent_*.py。
- 本地 runner 仅适用于自带的纯 Python 样例。路径限制、AST 检查、清理环境和超时不是操作系统安全沙箱。
- 三个more-itertools任务是MIT许可、固定提交的原样函数裁剪，属于回顾性开发任务，必须使用Docker；不扩大到任意仓库。默认列表仍为五个合成任务，CLI的`list --include-upstream`展示全部。不要将其称为独立未见基准或完整仓库修复。
- 没有经过真实 Docker 隔离验证前，禁止开放任意仓库上传、任意 shell 和依赖安装。
- 真实模型、离线回放、工程测试及评分结果分别记录；不编造提升和生产部署结果。
- 运行 pytest 和 Ruff，并将真实验证更新到 PROJECT_CONTEXT.md。
