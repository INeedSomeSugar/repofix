# v0.2 重复实验与 Docker 后端

本轮把一次性开发对照扩展到可冻结、可恢复的重复协议，同时实现可选 Docker 测试执行器。2026-10-26 保存的真实模型结果如下；所有20次均使用可信本地 runner。

| 策略 | 尝试 | verified | 实际 token | 耗时中位数 | p95 |
| --- | ---: | ---: | ---: | ---: | ---: |
| single_patch | 10 | 10 | 57,676 | 5.602秒 | 7.422秒 |
| feedback | 10 | 9 | 196,127 | 11.813秒 | 17.938秒 |

模型 `deepseek-flash`；5个自编合成开发任务 × 2策略 × 2重复。两策略按任务和重复序号交错顺序。反馈的 token 是单次补丁的约3.40倍，9组配对同时通过、1组仅单次补丁通过。任务较简单、样本少、没有外部保留集，本轮不能支持反馈提高修复率，也不能把10/10写成通用准确率。

完整 JSON 包含每次状态、token、时间、任务哈希和补丁。实验 ID：`d0b598aa020448a1a734ee341fb850be`；协议 SHA256：`bb5362bd623c7f97dbd4174daeddfe826907ee5e7690951fb1b3bfdbc7ba5dcc`；源码摘要：`197ccd6b976301b441697536f52dd5111ccd7b46eac508824e469c9f0f2ee50f`。见 [冻结试验](../reports/deepseek-repeated-v02.json)、[最终计划检查点](../reports/deepseek-repeated-v02.plan.json)、[证据清单](../reports/evidence/deepseek-v02/MANIFEST.json)。

## 一次具体失败

`merge_intervals` 的 feedback 第一次重复达到12轮上限。模型新增了与规范冲突的断言：把两个不重叠的点区间 `[3,3]` 和 `[4,4]` 期望合并成 `[3,4]`，随后围绕这条错误反馈反复修改。

结束后离线重测：冻结的原始公开测试与独立评分均通过；包含模型新增断言的测试仍失败。**原试验保持 budget_exhausted，不追加计为通过**。该案例说明模型生成的测试也是待检验假设，不能直接当作任务真值。下一轮可分开报告可信原测试与模型新增测试，核对新增断言与规范；提示词或状态规则变更必须建立新协议，不能回写本轮结果。

诊断以 [corrected JSON](../reports/budget-final-patch-audit-v02-corrected.json) 为准。首轮离线诊断误用了相对日志路径，导致测试基础设施错误；原文件保留并由 corrected 文件明确取代，不能将基础设施错误称作补丁评分失败。

## 冻结、恢复与复现

```powershell
cd D:\User\AI\repofix
.\.venv\Scripts\python.exe -m repofix.cli experiment status --id d0b598aa020448a1a734ee341fb850be
.\.venv\Scripts\python.exe scripts/verify_evidence.py --manifest reports/evidence/deepseek-v02/MANIFEST.json --report reports/deepseek-development-v02-runs.json
```

新的真实试验会消耗 API 用量：

```powershell
.\.venv\Scripts\python.exe -m repofix.cli experiment create --provider deepseek --cases csv_records rolling_average merge_intervals ttl_cache top_words --strategies feedback single_patch --repeats 2 --runner local
# 使用创建命令返回的新 ID
.\.venv\Scripts\python.exe -m repofix.cli experiment run --id <新ID>
.\.venv\Scripts\python.exe -m repofix.cli experiment export --id <新ID> --out reports/new-repeat.json
```

协议绑定任务、策略顺序、重复数、精确模型、源码和预算。每次试验新建工作副本，先保存运行ID再执行。完成的失败也不隐式重试；中断恢复保持原ID和预算。修改源码后拒绝继续旧协议。所有已尝试的上游错误、执行错误和预算结束进入分母，缺失用量留空。固定 replay 只统计工程回放通过情况。

## Docker 的当前状态

通过 CLI 显式 `--runner docker` 选择；网页仍使用默认本地 runner。Docker 不可用时在调用模型前失败，不回退本地执行。预检拒绝远程 daemon，仅使用本机 Linux 引擎和已存在镜像，随后固定真实镜像ID，禁止隐式拉取。

容器命令包含只读仓库/测试/harness、独立可写结果目录、禁网、只读根目录、非root、删除 capabilities、no-new-privileges、CPU/内存/PID/tmpfs上限。凭据不进入容器环境。超时后清理命名容器，检查不存在；daemon连接失败不算已清理。

2026-10-27补充：用户重启后Docker启动器出现注册项错误，修复既有入口后Linux引擎正常，官方Python镜像拉取成功。CSV容器回放完成“基线失败→修复后公开与独立测试通过”，清理确认。首次运行因Docker29小写不存在提示被误判未清理，原failed记录保留；兼容修复后新运行verified，见 [真实容器结果](../reports/docker-replay-20261027.json)。现为62项工程测试通过。这只验证实际执行与清理链路，完整隔离边界尚需专项测试，继续只接受内置可信样例。20次真实模型结果保持本地runner；本次replay没有模型调用。

## 可用于简历

> 基于 DeepSeek 工具调用实现 Python 代码修复 Agent，构建原始测试保护、独立评分、精确补丁及事务恢复；实现绑定代码与任务哈希的重复实验协议，记录20次真实开发试验的逐次结果和成本，并通过失败轨迹定位模型自生成回归断言导致的反馈偏差。实现可选 Docker 执行后端及不可用时的调用前阻断。

62项工程测试验证流程与约束；一次CSV容器回放不构成完整安全沙箱验证。
