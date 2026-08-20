# setup-matt-pocock-skills

> 首次使用这套工程 skill 前，为仓库配置三样东西：issue tracker、triage 标签词汇、领域文档布局。

## 1. 一句话理解

`setup-matt-pocock-skills` 是**一次性初始化**：其他工程 skill（`to-tickets`、`triage`、`to-spec`、`wayfinder`、`code-review`…）都假设仓库里已经有 `docs/agents/issue-tracker.md`、triage 标签映射、领域文档布局。本 skill 负责把这些"脚手架"建起来。

## 2. 它解决什么问题

`to-tickets` 要把任务发到哪里？`triage` 用什么标签字符串？`domain-modeling` 把 `CONTEXT.md` 放哪？这些如果没事先定好，每个 skill 运行时都要重新问一遍，甚至各跑各的。本 skill 一次性问清、写进 `docs/agents/*.md`，让后续 skill 读同一份约定。

## 3. 核心心智模型

**探索 → 呈现 → 确认 → 写入。** 这是一个 prompt 驱动的 skill，不是确定性脚本：先读仓库现状（`git remote`、`AGENTS.md`/`CLAUDE.md`、`CONTEXT.md`、`docs/adr/`、`.scratch/`、triage 是否已装、monorepo 信号），再把发现摆给用户，**一个 section 一个答案**地推进。

三个 section 各有默认姿态：A 有 GitHub remote 就默认 GitHub；B 只有 `triage` 已装才问标签；C 默认 single-context，只有发现 monorepo 信号才问 multi-context。

## 4. 一次典型运转

1. 探索仓库现状。
2. 逐 section 呈现推荐答案，用户一个字就能接受。
3. 写 `## Agent skills` 块到 `CLAUDE.md`（存在则编辑它，否则 `AGENTS.md`，二者不同时建），写 `docs/agents/issue-tracker.md`、`domain.md`、必要时 `triage-labels.md`。
4. 完成，告知哪些 skill 会读这些文件。

## 5. 何时用 / 何时不用

**用**：第一次用这套工程 skill 前，跑一次。

**不用**：已经配好、只想切 issue tracker 或重启才需要重跑。

## 6. 依赖与网络位置

- 是几乎所有工程 skill 的前置（它们读 `docs/agents/*.md`）。
- 附属：`issue-tracker-github.md`、`-gitlab.md`、`-local.md`、`triage-labels.md`、`domain.md` 等模板。

## 7. 易错点与坑

- **同时建 `AGENTS.md` 和 `CLAUDE.md`**：永远只编辑已存在的那一个，别两个都建。
- **问得太多**：能用推荐默认一笔带过的就别展开；B 在 `triage` 未装时直接跳过。
- **覆盖用户编辑**：`## Agent skills` 块已存在就原地更新，别追加重复块、别动周边内容。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/engineering/setup-matt-pocock-skills/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
