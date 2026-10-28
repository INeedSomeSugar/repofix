# RepoFix 项目上下文

最后更新：2026-10-28（Asia/Shanghai）。版本：0.3.0（反馈分层、重复停止及源码回滚，新增冻结三组对照）。本次发布前工程验证与展示文档已就绪，提交及远端核对由工作区发布记录保存。

## 当前状态

2026-10-28发布前完整91项工程测试通过，Ruff、格式、JavaScript语法及diff检查通过，JUnit `reports/publication-engineering-20261028.xml`。核对三组265文件证据和冻结源码，原始实验不回写；架构与演示文档同步当前七工具、分层反馈及实际对照结果，见`docs/DEMO_AND_INTERVIEW.md`。本轮整理交付与求职展示，没有新增模型调用或人工判断。

最新增量：三个新合成任务在首次生成模型调用前完成实际Docker准入、任务／代码／脚本／镜像／模型／预算冻结。单次补丁、旧反馈、分层反馈各运行三任务×两重复，共18次，三组各6/6通过；token总量分别36,410、137,080、205,800。106次真实响应均为`deepseek-flash`，用量完整；265文件证据及报告SHA256通过。未观察到额外通过收益，分层反馈token约为单次补丁5.65倍。两次分层运行出现自增断言冲突和受保护测试修改拒绝，保留原始轨迹，不补跑或调整成绩。三个任务已暴露，今后只能作为开发／回归任务。详见`docs/PROSPECTIVE_COMPARISON.md`。

当前完整91项工程测试通过，JUnit `reports/engineering-comparison-final-20261027.xml`。协议`9991e073ee6b404a81fef618df749c2d`及原始报告`reports/feedback-comparison-prospective-20261027.json`保持冻结，当前核心源码指纹`88d6470f0e65c5a16d268cbcbd1ca5b8edbc29c90b4fb1086c5fe6963956ada4`。源码归档及轨迹分析与旧实验分开，不合并统计。模型目录ID及实际响应ID不等于服务端权重快照。

v0.3新运行默认`layered_v1`：冻结原始测试和模型自增测试分进程运行，新增失败保留为待检验假设；全部通过且独立评分通过才可verified。若仅自增测试未解决、原始与独立测试通过，则needs_review。相同工作副本重复测试默认3次停止后评分，失败为stalled；停止后同批剩余调用取消。原始测试通过后保存仅源码的哈希检查点，显式恢复保留自增测试。旧记录缺少协议字段时仍按legacy_all读取，报告按协议分组，旧模型结果未重算。

上一轮78项工程测试通过，JUnit `reports/engineering-v03-20261027.xml`；Ruff及JavaScript语法检查通过。最终脚本在实际Docker固定镜像上验证错误断言→needs_review、重复状态→stalled、恢复后重新验证→verified三种合成轨迹，0模型调用。报告`reports/feedback-validation-v03-final-20261027.json`，3次运行的43个证据文件及报告SHA256核对通过。操作和可用表述见`docs/FEEDBACK_V03.md`。这一记录仅验证控制流程；真实模型对照见上方最新增量。

已发布独立公开仓库：https://github.com/INeedSomeSugar/repofix 。本轮新增三个MIT许可more-itertools原样函数裁剪任务，默认五个合成任务保持不变；CLI可显式列出和运行新任务，新任务强制Docker。父／修复提交、函数行号、原始文件与裁剪摘要、许可证、公开与独立测试摘要均保存。三个旧版本均被独立测试检出，冻结源码的修复回放全部通过。

68项工程测试及Ruff通过，JUnit `reports/engineering-upstream-20261027.xml`。真实`deepseek-flash`在三任务×两策略各一次共6次Docker运行、29次模型调用：两策略均3/3通过；single_patch 19,779 tokens，feedback 64,815 tokens，约3.28倍。耗时中位数9.969／20.968秒，没有观察到额外通过收益；不与旧20次合成任务混合统计，不称为未见基准。协议`5b958e96667947378e3f2c4650255e19`固定实际镜像ID，16个源码文件按协议摘要归档；87文件证据哈希核对通过。操作与原始结果见`docs/UPSTREAM_TASKS.md`。

独立项目位于 `D:\User\AI\repofix`，与 `knowledge-rag-lab` 分开。当前实现 DeepSeek 工具调用的显式 agent loop、七个受限工具、源码补丁、分层公开测试反馈、独立评分、持久化恢复、单次补丁对照、CLI 与本地网页。

v0.2增加可选Docker runner、调用前可用性阻断，以及冻结代码／任务／模型／预算的重复试验。CLI显式选择Docker，网页保持默认本地runner。2026-10-27用户已重启；Docker桌面／开始菜单／原自启动入口已备份修复，Linux引擎29.9.2正常。预检available=true，CSV真实容器回放和清理通过。

### 2026-10-27 实际Docker验证

- 专项探针实际通过10项：非root／零有效capabilities／no-new-privileges、源码／测试／harness与根文件系统写入阻断、results与tmp可写、tmp禁止直接执行、仅loopback且连接失败、凭据不继承且无Docker socket、cgroup实际内存／swap／CPU／PID配置、超额内存子进程被OOM终止、线程达到PID上限被拒绝。另两次实际触发timeout和output_limit，均未判通过且清理确认，无剩余RepoFix容器。原始证据`reports/docker-boundaries-20261027.json`，可复现脚本`scripts/verify_docker_boundaries.py`，无模型调用。只适用于本机可信工程探针，不等于任意代码安全认证。
- 已发布独立公开仓库`INeedSomeSugar/repofix`，源码与证据按原字节保存，运行目录和凭据不上传。发布基线工程验证62项通过；随后上游任务增量68项通过，分别保留两份JUnit。

- 原始入口读取缺失的旧注册项；已改为已安装的签名有效官方后端启动。停止后从桌面快捷方式重开，6.59秒内Linux Server就绪，无须重装或再次重启。
- 官方Python镜像ID：`sha256:12316debbfb86890f6b2d825820612741ba527ad5a44e3902759141d572bfe8f`。
- 首次CSV回放 `9c8b1c0e20bc4cd88abac7df2d3f332d` 实际测试已运行，但Docker29返回小写 `error: no such object`，旧代码大小写匹配导致清理未确认，原failed记录保留。
- 将清理错误判断改为casefold，仍要求退出码1及不存在提示；连接错误不算清理成功。新增两组格式覆盖，62项工程测试及Ruff检查／格式通过，JUnit为 `reports/engineering-docker-startup-20261027.xml`。
- 再次CSV回放 `f6f23f8743ec4c2f8b368b5371f64993` 为verified，基线2项有1项失败、修复后公开2项通过、独立4项通过、全部容器清理确认。`reports/docker-replay-20261027.json`。固定replay，无真实模型调用。
- 20次DeepSeek实验及原协议保持原样。修改前16个源码文件已按原摘要归档到 `reports/code-snapshots/197ccd6b976301b441697536f52dd5111ccd7b46eac508824e469c9f0f2ee50f.zip`；归档SHA256 `b1138d5cf311a4076b01314c9d6214b6dc961a9254d448dc398c1335cf758474`。当前代码与旧实验冻结代码不同，旧实验可离线查看，继续运行应建立新协议。

用户已明确授权复用现有 `DEEPSEEK_API_KEY`。本轮只从进程环境读取，未复制或写入任何密钥。不要读取或输出相邻项目的 .env。

五个原始合成开发任务：csv_records、rolling_average、merge_intervals、ttl_cache、top_words。参考修复只用于 replay；真实模型上下文不包含参考修复和独立测试。

## 验证快照

### v0.2 2026-10-26真实模型与工程快照

- 60项工程测试通过，Ruff通过；JUnit：`work/validation-v02/junit.xml`。Docker约束、清理异常、远程endpoint拒绝、不可用不回退、重复恢复及协议损坏检查均有覆盖，模拟测试不能代替真实隔离验证。
- `deepseek-flash`在五个合成开发任务上，两策略各重复两次，共20次真实运行，使用本地可信runner。single_patch 10/10、57,676 tokens；feedback 9/10、196,127 tokens，1次达到轮数上限。时间中位数分别5.602秒、11.813秒。没有观察到反馈收益。
- 实验ID `d0b598aa020448a1a734ee341fb850be`，协议SHA256 `bb5362bd623c7f97dbd4174daeddfe826907ee5e7690951fb1b3bfdbc7ba5dcc`。结果 `reports/deepseek-repeated-v02.{json,md}`；证据目录 `reports/evidence/deepseek-v02/` 共261文件，哈希校验通过。
- 达轮数上限的区间任务：原始公开测试和独立测试离线重测通过，但模型自增回归断言错误地合并两个不相接的点区间，全部公开测试失败。保留原始budget_exhausted，不补计通过。以 `reports/budget-final-patch-audit-v02-corrected.json` 为准，首轮相对日志路径造成基础设施失败的诊断保留并明确被取代。
- 操作、容器状态和可用简历表述：`docs/EVALUATION_V02.md`；重启后的检查：`../environment-setup/README.md`。
- 最终格式、JavaScript语法、25个包依赖兼容性通过；当前源码、任务与试验协议仍一致，261个证据文件哈希再次通过，本机健康API返回200。当前凭据原值在所选源码／文档／证据文件中未命中；摘要 `reports/local-validation-v02.json`。环境中的虚拟环境由uv管理、不含pip，依赖核验实际使用uv pip check。

### v0.1 历史记录

- 2026-10-26：47 项工程测试通过，覆盖真实子进程、全部五个回放任务、失败后继续修改、恢复、预算、事务幂等、环境清理、伪造 stdout 评分标记拒绝和 HTTP API。
- DeepSeek 模型目录连接通过，实际选择 `deepseek-flash`。
- CSV / 跨文件区间合并，各运行 feedback、single_patch，共四次真实模型运行均通过对应公开与独立测试。见 `reports/deepseek-development-v01.{json,md}`。
- feedback 两次累计 32,830 token / 26.437 秒；single_patch 两次累计 11,676 token / 13.563 秒。当前没有修复率差异，不能声称反馈提高准确率。
- 本地网页已启动，实际点击完成一次回放，页面展示“失败 → 通过”、独立评分、轨迹与实际补丁。
- 最终执行器重启后，网页再次实际完成回放；打开真实 DeepSeek 历史记录，确认任务选择、用量、补丁与评分对应，截图保存在 `docs/images/repofix-preview.png`。
- 最终执行器的五个回放任务全部通过，报告见 `reports/replay-pipeline-v01.{json,md}`；回放报告中的真实模型修复率保持 null。
- Ruff、JavaScript 语法和依赖兼容检查通过，Python wheel 实际构建成功。
- 四次真实模型运行已导出 54 个证据文件并通过 SHA-256 校验；扫描 102 个当时的可分享文件，未发现当前凭据原值。

## 实现决策

- 初版使用显式 Python 状态循环，未引入 LangGraph、多智能体或向量库。
- `deepseek-flash` 从实际 /models 响应选择；如用户指定模型，必须在目录中存在，不静默替换。
- 服务仅监听 127.0.0.1:8011，单 worker 队列，默认固定回放。
- 独立评分在模型结束后执行，不把评分反馈用于同一任务继续修复。
- 文件修改通过请求签名、前后 SHA-256 和事务意图恢复；读取和测试允许重跑。

## 已知限制

- 只处理五个原始合成任务、三个固定上游函数裁剪任务与三个新冻结合成任务；后两类仅用Docker。Docker已完成本机挂载／网络／权限／cgroup／OOM／PID／超时／输出上限／清理专项实测。任意仓库上传保持关闭，尚未进行对抗逃逸或通用安全审计。
- AST、路径和环境约束不是安全沙箱。
- 五个原始合成任务的20次真实模型试验与三个上游裁剪任务的6次试验均属于开发记录。新三个合成任务在首次模型运行前冻结并完成18次对照，但由本项目编写且未经独立人工审核、预训练污染未知；此后已暴露，不能继续作未触及保留集，没有完整上游仓库修复评测。
- token 停止阈值依赖上游用量，当前调用可能超出阈值；不等于严格计费上限。
- FastAPI/Starlette TestClient 使用 httpx 产生一条弃用提示，当前测试实际通过；后续依赖升级时处理。
- 本机沙箱限制默认临时目录及网络；测试在项目自己的 work 临时目录、授权执行环境中完成。这不是生产部署。

## 迭代记录

- v0.1.0：建立独立目录和依赖环境；实现核心 loop、工具、评分、恢复、CLI、网页和五个开发任务；完成真实 DeepSeek 对照。
- 验证时发现 Windows JSON 轮询读取会短暂阻止原子替换，增加有限重试和专门测试。
- 评分结果改为可信 harness 独立文件通道；不接受待测代码在 stdout 中打印的伪造通过标记。

## 下一步

1. 已完成重启、入口修复、官方镜像、真实CSV回放与本机边界专项验证，保存脚本和原始报告。
2. 三个固定开源函数缺陷已接入，完成实际容器验证及6次模型对照；后续再设计未见保留任务和更复杂依赖环境，当前不开放任意仓库。
3. 已完成三个首次模型运行前冻结任务的18次三组对照，没有观察到额外通过收益。下一步针对可见的自增断言冲突及调用成本提出明确改动，另建协议；当前任务用于回归，新独立任务与实际人工审核用于后续泛化评估。
