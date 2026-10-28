# 首次模型运行前冻结的合成任务对照

本轮对照围绕游标分页、库存事务和金额分配三个新任务，比较单次补丁、旧反馈与新分层反馈。任务在首次生成模型调用前完成工程准入和协议冻结。它们由本项目编写，独立测试仍由本项目维护；没有独立人工评审，无法确认模型预训练中是否见过类似问题。

## 实际结果：三组均通过，反馈消耗更多

2026-10-27，固定`deepseek-flash`在实际Docker中完成全部18次运行，无补跑、无缺失用量。接口返回的106条实际模型记录均为`deepseek-flash`，累计379,290 tokens。

| 组别 | 独立评分通过／全部尝试 | 实际token总量 | 模型调用 | 端到端耗时中位数 |
| --- | --- | --- | --- | --- |
| 单次补丁 | 6/6 | 36,410 | 18 | 11.258秒 |
| 旧反馈 | 6/6 | 137,080 | 42 | 19.782秒 |
| 分层反馈 | 6/6 | 205,800 | 46 | 24.242秒 |

旧反馈与分层反馈分别消耗单次补丁的约3.76和5.65倍token，分层反馈约为旧反馈的1.50倍。耗时包含模型、工具、Docker测试与最终独立评分，不是纯API延迟。这里只有三个不同任务，每组的六次运行包含两次重复；通过比例不代表通用修复率，也不足以作显著性或泛化结论。

轨迹中，两次分层反馈运行分别在浅拷贝和大整数分配的模型自增断言上出现冲突，均有两次“原始测试通过、自增测试失败”的分层反馈，之后通过`write_test`调整并最终通过独立评分。两次运行还分别发生1次和2次越权修改测试文件的尝试，被`replace_text`拒绝；其token用量为62,182和65,053。保留完整轨迹，不能据此把全部成本差异归因于单一机制。旧反馈也有两次运行各发生一次同类工具拒绝。

这一批次验证了新协议可以在真实模型调用中完成修复并保留分层记录，没有显示额外的通过收益。后续优化应以减少不必要调用和处理自增测试冲突为明确目标；任何改动都另建协议。当前默认协议保持原样，避免依据已经看过的任务回改本次结果。

原始[结果表](../reports/feedback-comparison-prospective-20261027.md)、[完整报告](../reports/feedback-comparison-prospective-20261027.json)、[轨迹审计](../reports/feedback-comparison-trace-audit-20261027.json)分开保存。265个导出证据文件及运行报告SHA256核对通过，包含18份实际响应模型／用量记录；[证据清单](../reports/evidence/feedback-comparison-prospective-20261027/MANIFEST.json)不含认证头。冻结源码归档在`reports/code-snapshots/88d6470f0e65c5a16d268cbcbd1ca5b8edbc29c90b4fb1086c5fe6963956ada4.zip`，归档SHA256为`9bf5cf03a48417ae4b3daea83a0cb63ed76873c31cebaaea48f23d657296f8bc`。

最终[本地核验摘要](../reports/local-validation-prospective-20261027.json)核对21份冻结源码／任务／比较脚本字节、106条响应与状态用量、18次评分及运行／准入基线记录中91个不同容器的清理确认。两个结束于62,182和65,053 tokens的运行超过60,000软停止阈值，按原始verified保留；见下方阈值说明。[运行环境快照](../reports/feedback-comparison-runtime-20261027.json)单独保存Python、依赖及Docker环境信息。

可用于面试的表述：实现受限工具调用、独立评分与可恢复执行，设计并冻结三组真实模型对照，记录通过情况及token成本；在三个合成任务的18次运行中，三组各6/6通过，反馈迭代用量更高，未宣称修复率提升。

## 任务与准入

| 任务 | 主要约束 | 不可见评分补充 |
| --- | --- | --- |
| `holdout_cursor_page` | 复合键分页、终页游标 | 迭代器、游标不在原数据中、浅拷贝、无副作用、limit类型 |
| `holdout_inventory_batch` | 库存非负、版本检查 | 同SKU连续变更、后段失败回滚、布尔值拒绝、空批次副本 |
| `holdout_money_allocation` | 整数守恒、最大余数与稳定排序 | 超大整数、迭代器、零权重、空输入及类型边界 |

默认网页和CLI仍列出原五个开发任务；`list --include-holdout`才展示新任务。新任务要求Docker。模型仅收到问题、原始源码与公开测试，参考修复及独立测试位于可见仓库之外。

[工程准入报告](../reports/holdout-admission-20261027.json)保存原始代码在真实Docker中的独立测试失败、参考回放通过、镜像ID、任务与源码SHA256。三个任务均通过准入，无模型调用。构建器`build_holdout_cases.py`只写不存在的文件，不覆盖已冻结任务。

## 冻结对照

协议ID：`9991e073ee6b404a81fef618df749c2d`。协议SHA256：`8dc5365195e599f0dae5b093370ab59b419a6d9eacc8563d92f11bc8ecfd00d4`。

| 组别 | 修复策略 | 反馈协议 |
| --- | --- | --- |
| single_patch | 首次补丁后独立评分 | legacy_all |
| legacy_feedback | 根据全部可见测试迭代 | legacy_all |
| layered_feedback | 根据分层反馈迭代 | layered_v1 |

三任务×三组×两次重复，共18次。按任务和重复序号旋转组别顺序，并在偶数重复反转，使三组在各执行位置上各出现两次。每次都使用新工作副本，模型会话不共享。相同任务的两次运行不是两个独立新任务。

固定目录验证可用的`deepseek-flash`、实际Docker镜像ID、代码／任务／比较脚本指纹、公开与独立测试、模型与工具停止阈值。温度0、非思考、非流式配置由冻结的provider源码决定。接口响应中的实际model、response_id和用量另存`provider-metadata.jsonl`，不保存认证头。远程服务未提供权重快照，目录ID相同不保证后台权重永久一致。

原始运行中的错误、预算耗尽、待复核及重复停止均保留；恢复时跳过已有终态，不自动补跑失败。报告分组保存全部尝试、状态分布、实际token及耗时分布。缺少用量时`total_tokens`保持null，已观察到的用量另列。单次补丁与反馈组拥有相同停止阈值，实际消耗可能不同。token阈值依据已返回的用量在下一轮调用前检查，一次响应及其工具批次可能越过阈值并完成；这是停止阈值，不是严格计费上限。

新反馈协议同时改变提示、测试分层执行、源码检查点工具和重复停止，三组比较检验的是整套协议，不能将差异归因于其中某一处。首次运行后，这三个任务已经暴露给模型；后续基于结果修改协议时，它们只能作为开发或回归任务，不能继续称作未触及的保留集。

## 复现

```powershell
cd D:\User\AI\repofix
.\.venv\Scripts\python.exe -X utf8 -m scripts.verify_holdout_cases --out reports/holdout-admission-new.json
.\.venv\Scripts\python.exe -X utf8 -m scripts.compare_feedback create --admission reports/holdout-admission-new.json --repeats 2 --provider deepseek
.\.venv\Scripts\python.exe -X utf8 -m scripts.compare_feedback run --id <comparison_id>
.\.venv\Scripts\python.exe -X utf8 -m scripts.compare_feedback export --id <comparison_id> --out reports/feedback-comparison-new.json
```

后两步也可在进程中断后恢复。`create`确认实际模型目录；`run`会发送合成代码任务并产生真实API用量。若只检查工程流程，创建时显式选择`--provider replay`，其结果不计模型修复率。所有报告采用新文件名，原记录不覆盖。

本轮完整91项工程测试通过，JUnit `reports/engineering-comparison-final-20261027.xml`；覆盖任务默认列表隔离、Docker要求、代码与任务变动拒绝、协议／试次绑定、错误不重跑、用量缺失和实际响应模型记录。旧v0.3核心源码已按原指纹归档，不回写旧实验。
