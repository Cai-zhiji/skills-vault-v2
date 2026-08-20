# scaffold-exercises

> 创建能通过 lint 的练习目录结构（section、problem、solution、explainer），用于搭课程练习骨架。

## 1. 一句话理解

`scaffold-exercises` 生成练习目录结构，让 `pnpm ai-hero-cli internal lint` 通过，然后 `git commit`。它是给 mattpocock 课程体系搭练习骨架的工具。

## 2. 它解决什么问题

课程的练习目录有一套严格的 lint 规则（命名、子文件夹、readme 非空、无 `.gitkeep`、无 `speaker-notes.md`、无断链、无 `pnpm run exercise` 命令……）。手搭容易触红线，本 skill 按规则生成，保证过 lint。

## 3. 核心心智模型

**目录命名**：section 用 `XX-section-name/`（`exercises/` 下），exercise 用 `XX.YY-exercise-name/`，dash-case。**变体子文件夹**：每个 exercise 至少一个 `problem/`（带 TODO 的学员工作区）/ `solution/`（参考实现）/ `explainer/`（概念材料，无 TODO）；打桩默认 `explainer/`。

**必需文件**：每个子文件夹一个 `readme.md`（非空、无断链）；有代码则另需 `main.ts`（>1 行）。打桩时 readme-only 即可。

**移动/重命名用 `git mv`**（保留历史），更新数字前缀，重跑 lint。

## 4. 一次典型运转

给定计划（Section 05 + 若干 exercise）：

1. 解析计划，提取 section/exercise 名与变体类型。
2. `mkdir -p` 建路径。
3. 每个变体文件夹建 readme 桩（标题 + 描述）。
4. `pnpm ai-hero-cli internal lint` 验证。
5. 报错就迭代修到过。
6. 提交。

## 5. 何时用 / 何时不用

**用**：要搭练习骨架、建练习桩、开新课程 section 时。

**不用**：不在这套课程体系里、不跑那个 lint 的场景。

## 6. 依赖与网络位置

- 依赖 `pnpm ai-hero-cli internal lint`。
- mattpocock 课程体系专用。

## 7. 易错点与坑

- **readme 留空**：即使一行标题也行，但必须非空。
- **留下 `.gitkeep` / `speaker-notes.md`**：lint 明确禁止。
- **用 `mv` 而非 `git mv`**：会丢 git 历史。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/misc/scaffold-exercises/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
