# teach

> 在本工作区内教用户一个新技能或概念——一个有状态、跨多会话的教学空间。

## 1. 一句话理解

`teach` 把当前目录变成一个**教学工作区**：用 `MISSION.md` 锚定学习动机，用 HTML `lessons/` 作为教学主单元，用 `reference/*.html` 存压缩知识、`learning-records/` 记学习记录、`RESOURCES.md` 管高可信资源、`NOTES.md` 记偏好。

## 2. 它解决什么问题

一般"教我 X"是一次性的、没有记忆的问答。`teach` 把学习当成**有状态的跨会话工程**：记录你为什么学、学到哪、下一步该学什么，让每次教学都接得上上次。

## 3. 核心心智模型

**知识 / 技能 / 智慧三分**，对应三种教法：

- **知识**（来自高可信资源）→ 用 `RESOURCES.md` 追踪，绝不信任参数化记忆。
- **技能**（通过交互式课程习得）→ 用 quiz、轻量浏览器任务，靠**紧反馈回路**练习。
- **智慧**（来自真实世界互动）→ 默认尝试回答，但最终**委托给社区**（论坛、subreddit、线下课）。

**流利强度 vs 存储强度**：流利（当下提取）会给人"已掌握"的错觉，存储（长期保留）才是目标。用**合意难度**设计课程——提取练习、间隔、交错（只对技能）。

**最近发展区（ZPD）**：每课让用户感到"刚好有点挑战"。读 `learning-records/` 判断他该学什么。

**课程是自包含的单个 HTML**，存 `lessons/0001-*.html`，要漂亮（Tufte 风格）、短、一课一个可把握的胜利，锚定 mission，链接其他课程/reference，推荐一手来源，并提醒可追问 agent。

**资产复用**：`assets/` 里存可复用组件（样式、quiz widget、模拟器），先读再建，别重复写。

## 4. 一次典型运转

1. `MISSION.md` 空就先用 `grilling` 问清"为什么学这个"。
2. 查 `RESOURCES.md`（薄就先找高可信资源）。
3. 判断 ZPD，设计一课（知识在前，技能靠交互回路练）。
4. 写 `lessons/0001-*.html`，复用 `assets/`，链接 reference 与一手来源。
5. 记录 `learning-records/`，更新 `NOTES.md` 偏好。

## 5. 何时用 / 何时不用

**用**：用户想学一个新技能/概念，且意图跨多会话。

**不用**：一次性问答（那不需要建教学空间）。

## 6. 依赖与网络位置

- 附属：`MISSION-FORMAT.md`、`RESOURCES-FORMAT.md`、`LEARNING-RECORD-FORMAT.md`。
- 是 `ask-matt` 的独立任务入口之一。

## 7. 易错点与坑

- **信任参数化记忆**：知识要从高可信资源找，别凭记忆。
- **课程太长**：工作记忆很小，一课要短、要单一胜利。
- **quiz 答案格式泄露线索**：每个答案字数（甚至字符数）相同，别用格式暗示答案。
- **mission 变了不更新**：mission 会随技能增长而变，要确认后更新并记 learning record。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/productivity/teach/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
