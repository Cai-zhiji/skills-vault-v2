# new-project

## 1. 一句话理解

这是一个把几乎空白的项目目录启动成“有决策记录、有术语、有状态、有本地提交”的可接手工程骨架的冷启动仪式。

## 2. 它解决什么问题

新项目最容易在第一天就失去方向：代码目录先被随意建满，关键决策只留在聊天里，下一位 agent 不知道目标、约束和下一步。`new-project` 先建立文档和目录的共同语言，再留下第一次 git commit，让项目从一开始就具备可恢复、可交接的上下文，而不是只有一堆空文件夹。

## 3. 核心心智模型

**先搭“导航层”，再让框架填“实现层”。** 项目骨架分成三层文档：`CLAUDE.md` / `AGENTS.md` 是给 agent 的精简指针，`CONTEXT.md` 是稳定的领域词汇和概念，`docs/STATUS.md` 是随时间变化的当前进度；目录则按功能域组织，`app/` 和 `server/` 保留给后续框架脚手架。

范围选择是另一个关键分叉：一个会话能理清的想法进入 `grill-with-docs`，复杂决策交给 `wayfinder`，明确规格则由 `to-spec` 产出 spec。无论走哪条路，结果都应是“后来的人能读懂项目为什么这样开始”，而不是机械创建一套与项目无关的目录。

## 4. 一次典型运转

调用时先检查工作目录是否基本为空；如果不为空，先让用户决定放入哪个子目录。接着在“大约一会话可理清的想法”“需要决策地图的复杂项目”“轻量快速起步”之间确定范围，并据此创建 `CONTEXT.md`、`docs/adr/` 或相关决策地图；若地图已包含 spec，就不重复生成。

范围明确后，根据 `templates/skeleton.md` 创建按功能域组织的树，空目录用 `.gitkeep`，不预填 `app/` / `server/`。再按模板生成 `CLAUDE.md`、`AGENTS.md` 和 `docs/STATUS.md`，把目标、进度和下一步写进去。最后创建 `.gitignore`，执行 `git init` 和首次本地 commit `chore: 项目初始化，建立文档化骨架`，展示骨架树与 STATUS 给用户确认；整个过程只操作本地 git，永不 push。

## 5. 何时用 / 何时不用

**适合用：** 新仓库、空目录、刚确定方向但尚未开始编码的项目，需要建立文档化起点和 agent 可接手上下文时。

**不要用：** 已有大量内容的仓库、只需要补一个功能、只想生成 spec、或只想更新当前状态时。已有项目应分别使用 `to-spec`、`grill-with-docs`、`wayfinder` 或 `session-end` 等更窄的 skill；不要把冷启动模板覆盖到现有工程上。

## 6. 依赖与网络位置

- 依赖 skill 目录内的 `templates/skeleton.md`、`CLAUDE-AGENTS.md`、`STATUS.md`、`gitignore.md`；依赖本地 git，但不依赖远程仓库或网络。
- 按范围选择时可接入 `grill-with-docs`、`wayfinder`、`to-spec`；它们负责澄清、决策地图或规格，不是本 skill 的目录模板本身。
- 与 `session-end` 形成生命周期上的前后关系：`new-project` 建立初始状态，`session-end` 在之后每次会话结束时维护状态和历史。
- 该 skill 是显式调用专用（Codex `$new-project`、Claude Code `/new-project`），兼容 Codex、Claude。

## 7. 易错点与坑

- 在非空目录直接写入，可能覆盖已有约定；必须先确认目标目录。
- 把 `app/`、`server/` 预填成自创实现；这两个目录应由实际框架脚手架决定。
- 混淆三层文档：入口指针写实现规则，`CONTEXT.md` 写进度，`STATUS.md` 写历史，会让交接信息迅速失真。
- 先建目录、后补范围，导致没有目标和决策依据；范围选择是必要检查点。
- 因为已经有远程仓库就 push；本 skill 的铁律是 local git only、永不 push。
- 只创建文件不做首次 commit，失去“项目从何时、以什么骨架开始”的可追溯基线。

## 8. 出处

- 原始路径：`my-skills/new-project/SKILL.md`
- 上游 commit：`51f963c`
- 平台兼容：Codex、Claude（Claude Code 支持 `disable-model-invocation` 扩展）

