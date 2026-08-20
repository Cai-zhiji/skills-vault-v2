# to-tickets

> 把计划/spec/对话拆成一组 tracer-bullet 任务（ticket），每个声明自己的阻塞边，发布到配置好的 tracker。

## 1. 一句话理解

`to-tickets` 把一份 spec 切成**垂直切片**的任务集，每个任务标出"被谁阻塞"，然后发布到 tracker（本地文件或 GitHub/Linear 等），让 agent 能按依赖顺序逐个认领。

## 2. 它解决什么问题

一份 spec 直接丢给 agent 实现会太大、太模糊。`to-tickets` 把它切成**每个都能塞进单个上下文窗口、每个都能独立演示/验证**的 tracer-bullet 切片，并用"阻塞边"显式表达依赖，让并发和顺序都清晰。

## 3. 核心心智模型

**垂直切片，不是水平分层切片。** 每个 ticket 是穿透所有层（schema/API/UI/测试）的一条窄而完整的路径，完成后可独立 demo/验证，且能塞进一个 fresh context window。

**阻塞边（blocking edges）**：每个 ticket 声明"必须等哪些 ticket 先完成"。没有阻塞的可以立即开工。发布时按依赖序（blockers first），在真 tracker 上用原生 blocking 关系，本地则用"每个 ticket 一个文件"。

**宽重构是垂直切片的例外。** 一个机械改动（改列名、改共享符号类型）爆炸半径跨全库，没有垂直切片能单独落地绿。这时用 **expand–contract**：先 expand（新旧并存）→ 按爆炸半径分批迁移（每批一个 ticket，被 expand 阻塞，逐批保持 CI 绿）→ 最后 contract（删旧形式）。

## 4. 一次典型运转

1. 从上下文取 spec（或读用户传的引用）。
2. 可选：探索代码库，找 prefactor 机会（"先让改变容易，再做容易的改变"）。
3. 拆垂直切片，给每个 ticket 阻塞边。
4. 向用户呈现代号列表（标题 / 被谁阻塞 / 交付什么），问粒度对不对、阻塞边对不对、要不要合并/拆分，迭代到批准。
5. 发布到 tracker：本地一个 ticket 一个文件（`.scratch/<slug>/issues/<NN>-<slug>.md`，`01` 起按依赖序）；真 tracker 一个 issue 一个 ticket。标 `ready-for-agent`。

## 5. 何时用 / 何时不用

**用**：有一份计划/spec/对话要拆成可执行任务时。

**不用**：任务小到一张 ticket 就能装下；还在澄清阶段（先 `to-spec`）。

## 6. 依赖与网络位置

- 依赖 `setup-matt-pocock-skills`（tracker 与标签）。
- 是 `ask-matt` 交付链、`wayfinder` 之后的关键一环。
- 产物直接可被 `implement` 消费，不必再过 `triage`。

## 7. 易错点与坑

- **水平切片**：按层切（先全部 schema、再全部 API…）是错的，要垂直穿透。
- **把宽重构硬塞成 tracer bullet**：要用 expand–contract 序列，别让它单独炸 CI。
- **改动/关闭父 issue**：明确禁止——只建子任务。
- **写文件路径/代码片段**：会过时；只写行为与验收标准。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/engineering/to-tickets/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
