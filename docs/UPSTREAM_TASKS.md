# 三个固定上游缺陷任务

从more-itertools的真实MIT许可修复提交，提取相关函数的原始版本和修复版本。函数正文及docstring按AST行号原样提取，仅增加出处注释、改变模块路径为`project.core`。无需安装整个上游包；运行环境为现有Python 3.12容器和标准库。

| 任务 | 缺陷 | 上游修复 |
| --- | --- | --- |
| upstream_value_chain | 消费迭代器期间的TypeError被误当作不可迭代参数 | [7847d432](https://github.com/more-itertools/more-itertools/commit/7847d4324a581da8d0919734a8e50b2a6573b780) |
| upstream_split_empty | 三个split函数在maxsplit=0时为空输入输出额外空分组 | [ce676d24](https://github.com/more-itertools/more-itertools/commit/ce676d24136e6efa932df8a4f3bf4801b89e1dd0) |
| upstream_custom_exception | one/only丢弃假值自定义异常，并提前计算默认错误消息 | [def2dabe](https://github.com/more-itertools/more-itertools/commit/def2dabea858b6ecb84ee0c52e6e07929f2c409c) |

每个任务的`provenance`保留父提交／修复提交、完整原始文件URL与SHA-256、函数起止行与摘要、裁剪模块摘要、许可证摘要及测试摘要。许可证见[原始许可证](../third_party/more-itertools/LICENSE)，运行副本也包含`LICENSE.md`。

公开和独立测试由本项目依据上游回归条件编写；独立测试在模型完成后评分，不进入模型工具目录。它们是回顾性裁剪开发任务，尚未建立独立人工审核的未见保留集，不代表完整上游仓库修复或SWE-bench表现。原五个合成任务、默认网页列表和旧实验均保留原样。

## 运行与重建

```powershell
.\.venv\Scripts\python.exe -m repofix.cli list --include-upstream
.\.venv\Scripts\python.exe -m repofix.cli run --case upstream_value_chain --provider replay --runner docker
.\.venv\Scripts\python.exe -X utf8 scripts/verify_upstream_cases.py --out reports/upstream-replay-new.json
```

上游任务强制Docker，本地runner会在创建运行前拒绝。生成实验协议时固定实际镜像ID；模型调用前仍需通过Docker预检，不回退到本地。

2026-10-27三任务的旧代码均在实际容器中被独立测试检出；上游修复回放后公开及独立测试均通过。正式冻结代码记录：[回放](../reports/upstream-replay-frozen-20261027.json)、[旧代码独立测试](../reports/upstream-replay-frozen-20261027-baseline-independent.json)。开发期间首轮回放仍保留在`upstream-replay-20261027.*`，复现以冻结版本为准。回放不计模型修复率。

## 真实模型开发对照

`deepseek-flash`在三任务上分别运行反馈与单次补丁，每种策略每题一次，共6次实际运行、29次模型调用，合计84,594 tokens。所有测试使用同一个冻结Python镜像，结束后容器清理确认。

| 策略 | 通过 | tokens | 每次运行耗时中位数 |
| --- | --- | --- | --- |
| single_patch | 3/3 | 19,779 | 9.969秒 |
| feedback | 3/3 | 64,815 | 20.968秒 |

本批次没有观察到反馈策略额外通过收益，token用量约3.28倍。任务小、同一上游来源且每题仅一次，不能据此推断一般修复率。与此前20次合成任务、本地runner实验分开报告。

协议ID：`5b958e96667947378e3f2c4650255e19`；协议SHA-256：`b4fd065fe4f4ecdbda0d19c7374c12786f1f94eeabacbb74a58cc881cb2248fc`。代码SHA-256：`bd3fdfb6f9fbf2182c5d9a5ccf74be449bac841e7c0e40a0024e074f3fcdf859`，对应16个源码文件已按摘要归档，ZIP内逐文件哈希及CRC核对通过。

查看[配对结果](../reports/deepseek-upstream-20261027.md)、[原始JSON](../reports/deepseek-upstream-20261027.json)、[逐运行报告](../reports/deepseek-upstream-runs-20261027.json)。87个原始消息／事件／补丁／前后源码文件随[证据清单](../reports/evidence/deepseek-upstream-20261027/MANIFEST.json)导出并通过哈希验证。

可从固定官方URL重新下载快照再生成任务；下载步骤只保存文件并静态解析AST，不执行下载代码：

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/build_upstream_cases.py --fetch
```

默认不联网，读取`work/upstream/`缓存。重建会更新`fixtures/upstream.json`，应检查Git差异；旧实验根据任务摘要拒绝恢复到变化后的任务。
