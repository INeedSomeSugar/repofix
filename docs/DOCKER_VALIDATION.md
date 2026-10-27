# 本机Docker专项验证

2026-10-27在Windows / WSL2、Linux Docker Engine 29.9.2上，使用项目实际`DockerRunner.run_tests`执行可信工程探针，无模型调用。原始结果：[docker-boundaries-20261027.json](../reports/docker-boundaries-20261027.json)。

| 场景 | 实际结果 |
| --- | --- |
| 正常边界探针 | 10项测试通过，输入哈希不变，容器清理确认 |
| 超时 | 2秒停止阈值触发timeout，不判通过，容器清理确认 |
| 输出超限 | 超过2,000,000字节触发output_limit，不判通过，容器清理确认 |

10项覆盖非root与有效权限、只读挂载、可写结果／临时目录、tmp禁止直接执行、仅loopback且外部连接失败、凭据隔离／无Docker socket、cgroup实际配置、超额内存子进程OOM终止、PID达到上限拒绝创建线程，以及运行期间Docker inspect。inspect记录实际用户、挂载RW、禁网、只读根目录、capabilities、安全选项与资源配置。CPU检查读取cgroup配额，没有通过负载测试测量CPU吞吐。

实际限制：256MiB内存、无额外swap、64 PID、1 CPU配额、32MiB临时目录。镜像以预检得到的不可变image ID运行，不自动拉取。最终无剩余RepoFix容器。

复现前先确保本机Linux Docker engine和`python:3.12-slim`镜像可用：

```powershell
.\.venv\Scripts\python.exe -m repofix.cli runner-check --image python:3.12-slim
.\.venv\Scripts\python.exe -X utf8 scripts/verify_docker_boundaries.py --out reports/docker-boundaries-new.json
```

脚本拒绝覆盖历史报告。探针只操作自己创建的容器和`work/`目录。此结果验证本机配置与故障清理行为；任意仓库上传、任意shell与依赖安装仍保持关闭，未进行对抗逃逸测试。
