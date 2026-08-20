# to-spec

> 把当前对话合成一份 spec 并发布到 issue tracker——不做访谈，只是把你已经讨论过的东西综合起来。

## 1. 一句话理解

`to-spec` 是**纯综合**：不拷问用户，把当前会话上下文 + 代码库理解，直接整理成一份结构化 spec，发到 issue tracker，并标 `ready-for-agent`。

## 2. 它解决什么问题

需求澄清到一定程度后，需要把散落在对话里的决定沉淀成可执行的 spec。`grilling` 负责问，`to-spec` 负责"不问、只综合"——它假设该讨论的已经讨论完，现在是把共识转成规格的时刻。

## 3. 核心心智模型

**spec 是决定清单，不是代码。** 结构固定八节：Problem Statement（用户视角的问题）、Solution（用户视角的方案）、User Stories（很长、编号、`As a … I want … so that …` 格式、覆盖所有方面）、Implementation Decisions（模块/接口/技术澄清/架构/模式/API 契约，**不写具体文件路径和代码片段**）、Testing Decisions、Out of Scope、Further Notes。

**接缝先于规格。** 写 spec 前先勾勒要测试的接缝，优先复用已有接缝、取最高点；理想数量是一个。接缝定了再写 spec。

**一个例外**：如果原型产出的片段（状态机、reducer、schema、类型形状）比散文更精确地编码了某个决定，可以内联，注明来自原型。

## 4. 一次典型运转

1. 探索代码库，用领域词汇说话。
2. 勾勒接缝并和用户确认。
3. 按模板写 spec，发 issue tracker，标 `ready-for-agent`（无需再 triage）。

## 5. 何时用 / 何时不用

**用**：对话已经澄清、需要把共识落成规格时。

**不用**：还需要继续追问澄清（先 `grilling`/`grill-with-docs`）；对话里信息不足以综合出 spec 时。

## 6. 依赖与网络位置

- 依赖 `setup-matt-pocock-skills` 配好的 tracker 和标签。
- 是 `ask-matt` 主交付链、`wayfinder` 终点的关键一环。
- 与 `to-tickets` 衔接：spec 之后拆任务。

## 7. 易错点与坑

- **去访谈用户**：明确禁止——只综合已知，别问新问题。
- **写具体文件路径/代码片段**：会迅速过时，只写决定。
- **接缝没先和用户确认**：接缝是测试的锚点，要先对齐。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/engineering/to-spec/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
