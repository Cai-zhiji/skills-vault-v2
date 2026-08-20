# ask-matt

> 根据你当前工作的起点、规模和不确定性，告诉你该调用哪个 skill、按什么顺序衔接。

## 1. 一句话理解

`ask-matt` 是整个 mattpocock skill 集的路由器。它不实现任何功能，只做一件事：判断你处在哪种工作情境，然后推荐下一步该进哪个 skill，以及之后怎么串起来。

## 2. 它解决什么问题

这一套 skill 有 35 个，各自负责一块流程（澄清需求、写规格、拆任务、实现、评审、诊断 bug……）。一个人面对任务时最难的往往不是"某个 skill 怎么用"，而是"我该先跑哪个、跑完接哪个"。`ask-matt` 把这个编排问题接管过去：你只需描述当前处境，它输出一条路径。

## 3. 核心心智模型

**用"起点状态"来分诊。** 它把工作起点归为四类，每类对应一条进入链：

- **从想法开始**：`grill-with-docs` 澄清 → `to-spec` 成规格 → `to-tickets` 拆任务 → `implement`。
- **从外部问题开始**：`triage` 整理成可执行问题。
- **从顽固故障开始**：`diagnosing-bugs` 建反馈回路。
- **大型未知项目**：`wayfinder` 建决策地图 → `to-spec` → `to-tickets`。
- **独立任务**：研究、原型、教学、问卷、向导等，不进完整交付链。

它还维护一条"阶段边界"决策：一个阶段结束、下一阶段开始时，判断是继续当前会话、`clear`、`handoff`、交给子 agent、还是 `compact`——本质是"上下文怎么在阶段之间流动"。

## 4. 一次典型运转

你说"我想给这个仓库加一个还不确定怎么做的功能"：

1. `ask-matt` 识别为"有模糊想法"→ 推荐 `grill-with-docs`（边问边把术语和决策写进 `CONTEXT.md`/ADR）。
2. 澄清到规格可写 → `to-spec` 合成 spec 发到 issue tracker，标 `ready-for-agent`。
3. 规格要跨会话实现 → `to-tickets` 拆成带阻塞边的 tracer-bullet 任务。
4. 每个任务进 `implement`（内部用 `tdd` 红绿循环），结束前 `code-review` 双轴审查。

中间如果某个设计问题只能靠可运行代码回答，插入 `prototype`；如果只有人能完成某步（配凭据等），用 `wizard`。

## 5. 何时用 / 何时不用

**用**：知道目标但不确定该调哪个 skill，或不确定多个 skill 的衔接顺序。

**不用**：已经明确且只需执行的小任务——直接进 `implement`/`tdd` 即可，不必路由。

它只负责选路径，**不替代**被选中的 skill；`wayfinder` 消除大型项目的决策迷雾、`codebase-design` 负责模块/接口语言、`domain-modeling` 负责领域词汇——这些分工各自独立。

## 6. 依赖与网络位置

- 是这套 skill 的顶层入口，被 `setup-matt-pocock-skills` 铺垫（先跑后者配好 issue tracker、标签、领域文档布局）。
- 它"指向"几乎所有其他 skill，但不依赖它们运行。
- 触发策略：仅显式调用（`/ask-matt` / `$ask-matt`）。

## 7. 易错点与坑

- **把路由当执行**：`ask-matt` 只指路，别指望它自己产出代码或文档。
- **`to-tickets` 产物不必再过 `triage`**：`triage` 只处理未经整理的外部输入，`to-tickets` 出的任务已经可执行。
- **阶段切换别急着压缩上下文**：优先继续当前会话，把独立部分交给子 agent，而不是为了腾空间去 `compact`。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/engineering/ask-matt/SKILL.md`（另含 `PHASE-BOUNDARIES.md`）
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
