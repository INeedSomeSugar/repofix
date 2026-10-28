# v0.3 反馈分层与恢复

2026-10-27，本地工程增量。旧版真实DeepSeek实验中出现模型新增错误断言后反复修复的问题，本版将测试来源显式拆开，并提供停止与恢复路径。旧实验和冻结源码归档均保留原字节。

## 新运行的规则

默认`layered_v1`将冻结原始测试与`tests/test_agent_*.py`分别放进测试快照、由独立进程执行，两层共享本次工具调用的时间预算。反馈包含各层计数、失败输出及工作副本哈希；模型新增断言是需要对照问题说明检查的假设。独立评分仍只在停止后执行，断言和结果不回灌给同一次修复。

| 最终条件 | 状态 |
| --- | --- |
| 有源码变更，原始、自增（若有）及独立测试全部通过 | `verified` |
| 有源码变更，原始与独立通过，仅自增测试仍未解决 | `needs_review` |
| 相同工作副本重复测试达到阈值，最终仍有失败 | `stalled` |
| 正常结束仍未满足通过条件 | `failed` |

重复计数绑定整个受管工作副本哈希，默认阈值3次。恢复运行保留计数；触发后取消同批剩余工具调用并冻结补丁评分。基础设施错误不计入重复测试次数。这是对重复测试的约束，不能保证识别所有无效推理循环。

原始测试通过会保存源码检查点。`restore_checkpoint`只恢复该检查点中的源码，校验清单与每个文件SHA256，并通过文件事务支持重复恢复；模型自增测试继续保留。检查点只代表原始测试曾通过，恢复后仍需重新测试，不能直接判为修复成功。

## 复现

```powershell
cd D:\User\AI\repofix
.\.venv\Scripts\python.exe -X utf8 -m scripts.verify_feedback --output reports/feedback-validation-new.json
```

默认要求本机Docker就绪，固定实际镜像ID；Docker不可用时直接失败，不回退本地执行。脚本使用固定合成provider，执行三种轨迹，不调用模型。输出文件必须采用新名称。普通CLI也可显式指定协议：

```powershell
.\.venv\Scripts\python.exe -m repofix.cli run --case rolling_average --provider replay --feedback-policy layered_v1
.\.venv\Scripts\python.exe -m repofix.cli evaluate --provider replay --feedback-policy legacy_all --out reports/legacy-replay-new.json
```

`run`、`evaluate`和`experiment`都记录协议；旧运行没有该字段时按`legacy_all`读取。报告按provider、实际模型ID、策略及反馈协议分组。重新比较模型表现需要建立新冻结协议，不能将本次合成回放补计进旧26次模型实验。

## 已保存验证

- 完整78项工程测试通过：[JUnit](../reports/engineering-v03-20261027.xml)。覆盖分层失败、损坏检查点拒绝、幂等恢复、暂停恢复后重复计数、停止后取消工具、旧协议读取和报告分组。
- [最终Docker回放](../reports/feedback-validation-v03-final-20261027.json)：错误断言→`needs_review`、重复状态→`stalled`、源码回滚及重测→`verified`，三项均符合预期。固定镜像ID和脚本／源码指纹在报告中。
- [逐次运行报告](../reports/feedback-validation-v03-final-20261027-runs.json)及Markdown保留；本机导出43个证据文件，含检查点清单，哈希核对通过。

```powershell
.\.venv\Scripts\python.exe scripts/verify_evidence.py --manifest reports/evidence/feedback-v03-final-20261027/MANIFEST.json --report reports/feedback-validation-v03-final-20261027-runs.json
```

面试可表述：针对模型自增断言造成的错误反馈，实现测试来源分层、重复状态停止和哈希检查点恢复，并用真实Docker中的固定合成轨迹验证。随后另建冻结协议完成18次真实模型三组对照，三组各6/6通过，分层反馈token约为单次补丁5.65倍，未观察到额外通过收益；详见[协议及结果](PROSPECTIVE_COMPARISON.md)。本节78项测试及固定回放是此前工程快照，不与后续91项完整测试和真实模型结果混算。
