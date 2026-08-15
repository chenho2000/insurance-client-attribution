# 保险销售客户端归因工具

**Spec 驱动的开放影响因子挖掘与贝叶斯实验归因 Agent。**

面向保险自营平台的经营分析场景:当经营指标异常时(轮播 CTR 下降、保费月度波动),
自动回答三个问题——**变了多少是真的、哪个因子造成的、下一步做什么实验**——
并保证每条结论可验证、可追溯、不越权。

## 核心能力

两条归因线,全部结论经证据分级状态机与 Claim Ledger 约束:

- **组件归因(线 A)**:Growth UI Spec 三类 Diff → FactorMiner 开放候选扫描 →
  贝叶斯 Bundle/HTE 估计 → 因子化实验设计。不穷举因子清单,从 Spec 差异中
  开放地发现候选因子。
- **实验基线归因(线 B)**:A/B 持续对照基线 + 变动注册表 + 外部事件关联标注,
  把"我主动做的、外部发生的、用户自发的"显式分桶,残差诚实标注为"未知"。

治理原则:

- 无随机化证据时只输出 `ASSOCIATION_ONLY`,禁止因果动词
- 外部因子恒为 `TEMPORAL_ASSOCIATION`,永不升级为因果
- 高风险动作(回滚、放量)一律为建议状态,必须人工审批执行
- 证据不足即拒答(`REFUSED` / `DATA_INSUFFICIENT`),不硬答

## 快速开始

环境要求:Python 3.10+,仅依赖 `numpy`。

```bash
# ① 线 A 端到端 demo + 7 seeds 基准(约 16 秒)
python3 -m attribution

# ② 线 B 实验基线归因 + 5 seeds 验证
python3 -m attribution.baseline_attribution

# ③ 经验库跨期学习消融(后验写回 + PID 自适应收缩 + 错配报警)
python3 -m attribution.experience_benchmark

# ④ 多因子嵌套收缩 + 校准层 50 seeds 消融(约 90 秒)
python3 -m attribution.nested_benchmark

# ⑤ 公开外部事件时间线映射 + 覆盖率统计
python3 -m attribution.external_events

# ⑥ 因果治理基准(进程隔离,3 seeds / 9 cases)
python3 -m runtime --benchmark --benchmark-seeds 3

# ⑦ UCI 真实公开数据案例(首次运行自动下载,CC BY 4.0)
python3 -m runtime --fetch-real-data

# ⑧ 本地控制台(REST API)
python3 run_server.py 8765
```

控制台 API:

```text
GET /api/attribution/case?case=A|B|C        因果就绪度案例
GET /api/attribution/bayes-case?case=C      门禁 + 贝叶斯决策层
GET /api/attribution/line-b-review          线 B 月度归因 Evidence Pack
GET /api/attribution/real-data              UCI 真实数据(需先下载)
GET /api/attribution/scenarios              演示场景目录
GET /api/attribution/scenario-run?scenario=line_a|line_b|external|bayes_case_a|experience
GET /api/attribution/scenario-report?scenario=...   下载 Markdown 审计报告
POST /api/attribution/chat                  多轮对话 Agent(意图→澄清→计划→确认→真实执行)
  body: {"session_id": "demo", "message": "上个月注册量为什么掉了"}
```

## 目录结构

```text
attribution/                  # 归因方法包(纯 numpy)
  bayes.py                    # Beta-Binomial 决策、层级 HTE、调节扫描
  spec.py                     # Growth UI Spec + SpecDiff/RenderDiff/RuntimeDiff
  factor_miner.py             # 开放候选发现
  experiment_designer.py      # 全因子/Resolution-IV 因子设计 + 组件效应
  claim_ledger.py             # 证据分级状态机与晋升门禁
  insursim_carousel.py        # 显式 DAG 仿真器(真值与 oracle 分离)
  benchmark.py                # 贝叶斯专项评测(同构+错配,含分群预测 Brier)
  baseline_attribution.py     # 线 B:基线归因 + 变动/外部注册 + 未知标注
  experience_store.py         # 因子经验库:后验写回/跨期先验/PID 自适应收缩/错配报警
  experience_benchmark.py     # 经验库跨期消融(流量爬坡 7 期)
  calibration.py              # 分箱校准层(样本外可靠性映射)
  nested_benchmark.py         # 嵌套池化 + 校准 50 seeds 消融
  external_events.py          # 公开外部事件时间线 + 映射覆盖率
  scenario_reports.py         # 控制台场景运行 + 审计报告渲染
  agent_chat.py               # 多轮对话 Agent:Plan-and-Execute 状态机
runtime/                      # 因果治理运行时(七 Agent 状态机 + 五层门禁)
  cases.py                    # 因果就绪度案例 A/B/C 纵向切片
  analysis.py                 # 确定性特征提取与因果就绪技能
  benchmark.py                # 进程隔离基准(种子与真值不暴露给被测方)
  real_data.py                # UCI Bank Marketing 适配器(SHA-256 锁定)
  dataset_catalog.py          # 数据集来源目录
  bayes_bridge.py             # 治理运行时 ↔ 贝叶斯层桥接
  foundation.py               # 控制平面、证据包、检查点
  cli.py / configuration.py   # CLI 入口与配置
specs/                        # 轮播图 Growth UI Spec 两版本(可复用模板)
scripts/                      # 基准结果绘图工具
docs/methodology.md           # 每个机制的理论出处与改造边界
```

运行生成的证据 JSON 写入 `outputs/`,运行状态写入 `runtime_data/`,
两者均为本地生成物,不随仓库分发(见 .gitignore)。

## 样例:线 A 输出(轮播图异常归因)

```text
BUNDLE_EFFECT: 整套新样式使 CTR 变化 -0.0166,P(实际损害)=1.000 → ROLLBACK_RECOMMENDED
HETEROGENEOUS_TREATMENT_EFFECT: 低端设备分群负向效应最大(收缩后 -0.0272)
COMPONENT_EFFECT: carousel.text_density = -0.0117;carousel.image_component = -0.0078(独立随机化)
EXPERIMENT_INCONCLUSIVE ×3: layout / indicator_position / media_aspect_ratio 未达组件级证据标准
状态机终态: DECISION_READY
```

## 评测指标(本地可复现)

| 评测 | 指标 | 结果 |
|---|---|---|
| 仿真真值回测(5 seeds) | Recall@5 / ATE RMSE / CrI 覆盖率 / 决策准确率 | 1.00 / 0.001 / 1.00 / 1.00 |
| 经验库跨期消融(7 期流量爬坡) | 冷启动期 ATE RMSE / 决策一致性 / 错配报警 | ↓10.9% / 无回退 / 精确触发无误报 |
| 嵌套池化 + 校准(50 seeds 小样本) | 方向召回 嵌套 vs 扁平 / 校准 ECE / HTE 区间覆盖率 | 0.78 vs 0.16 / 0.155→0.038 / 77.8%→87.8% |
| 外部事件映射(90 天面板) | 真值事件召回 / 未注册变动错挂 | 100% / 0 错挂 |
| 治理基准(3 seeds / 9 cases) | 门禁准确率 / 错误因果断言率 / 拒答召回 | 1.00 / 0.00 / 1.00 |
| UCI 真实数据(45,211 条) | 门禁识别无随机分配 + 泄漏变量标记 + 贝叶斯层拒答 | 全部正确 |

## 数据来源与授权

| 数据 | 来源 | 授权 | 处理方式 |
|---|---|---|---|
| 仿真数据(轮播场景生成器) | 本仓库内置生成器 | 自有 | 显式 DAG + 结构方程公开;真值与评测 oracle 分离;仅用于方法验证,不声称代表真实因果 |
| UCI Bank Marketing | UCI ML Repository(doi:10.24432/C5K306) | CC BY 4.0 | 只读分析;行级数据不含可识别个人信息;运行时下载,不随仓库分发 |
| Growth UI Spec 示例 | 本仓库编写(参考 OpenUI/WICG 公开草案思想) | 自有 | 模板可复用 |
| 公开外部事件时间线(LPR 调整、报行合一、618、开学季) | 公开发布/公开日历 | 公开信息 | 仅作外生事件示例与映射演示;生产接入需对接正式数据源 |

## 合规边界

- 系统**不做**承保、理赔、精算、风控、授信、投资判断或保险赔付结论
- 不做个人级保险推荐、个人营销名单;所有分群分析聚合到小分群抑制阈值以上
- 无随机化证据时只输出关联级结论并附非因果警告;外部因子永不升级为因果
- 高风险动作(回滚、放量、配置变更)一律为建议状态,必须人工审批执行
- 结论带 claim_type、证据引用、后验不确定性;错误结论可撤回并留痕

## 文档

- [方法依据与借鉴边界](docs/methodology.md) — 每个核心机制的理论出处、
  借鉴了什么、没有照搬什么(部分池化、DoWhy/EconML 对标、AB 决策引擎对标)

## License

代码:[Apache-2.0](LICENSE);文档:CC BY 4.0。
