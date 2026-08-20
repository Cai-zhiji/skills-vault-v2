---
name: skill-guide-writer
description: 为 skills-vault 里的 skill 撰写或重写 8 节重述式中文说明文档。Use when the user asks to 写/制作/生成/重写 skill 说明文档、单个 skill 的说明、批量说明文档、全部 skill 说明、或上游 SKILL.md 更新后刷新说明。Single mode reads one skill's SKILL.md and rewrites it into 8 sections; batch mode iterates catalog.json over every skill. Output lands in docs/skill-guides/<source>--<name>.md.
---

# skill-guide-writer

为 Skills Vault 的 skill 写**深度说明文档**。目标不是路由、不是复述原文，而是**让读者深入理解这个 skill 的作用**——用 8 节骨架，重述式地讲透。

## 产出位置与命名

每篇说明是一个 Markdown 文件，路径固定：

```text
docs/skill-guides/<source>--<skill-name>.md
```

`<source>` 和 `<skill-name>` 来自 catalog 里该 skill 的 `id`（`<source>/<name>`，把 `/` 换成 `--`）。例如 `mattpocock/grilling` → `docs/skill-guides/mattpocock--grilling.md`。这个路径是网页端 `/skills/<id>` 渲染所依赖的，不可改。

## 8 节骨架（核心契约）

每篇说明严格用这 8 个 `##` 二级标题，顺序固定，不多不少：

```text
# <skill-name>

## 1. 一句话理解
## 2. 它解决什么问题
## 3. 核心心智模型
## 4. 一次典型运转
## 5. 何时用 / 何时不用
## 6. 依赖与网络位置
## 7. 易错点与坑
## 8. 出处
```

每节写什么：

1. **一句话理解**——用你自己的话定义这个 skill，**不是** catalog 里那句 description 的翻译。一句话说清"它是什么"。
2. **它解决什么问题**——动机与痛点：缺了它，用户会被什么卡住。写"为什么需要它"，不写"它有哪些功能"。
3. **核心心智模型**——★ 全篇主战场。抓住这个 skill 赖以运转的**那一个关键概念或比喻**（grilling 的"设计树/前沿"、diagnosing-bugs 的"变红回路"、codebase-design 的"深模块"）。懂了它，其余顺理成章。这是手写独有的、机器产不出的部分。
4. **一次典型运转**——端到端走一遍真实使用场景。**重述**流程，不照搬原文步骤编号。
5. **何时用 / 何时不用**——边界：什么情况用它、什么情况不用它、不用它时用哪个相近 skill。
6. **依赖与网络位置**——它依赖谁、被谁依赖、与谁冲突（同名冲突要标注）。**没有依赖就整节省略**。
7. **易错点与坑**——高频报错、反模式、与原文的差异、踩过的坑。
8. **出处**——`原始路径`（`skill['path']`）、`上游 commit`（`skill['source_commit'][:7]`）、平台兼容。

## 单一制作流程

用户指定一个 skill（名字或 id）时：

1. 从 `catalog/catalog.json` 找到该 skill 的条目，拿到 `id`、`path`、`source_commit`、`name`。
2. **完整读** `<skill['path']>/SKILL.md` 正文——重述式的前提是读全，不只看 description。
3. 按 8 节骨架重述：中文优先，术语、标题、命令、代码、示例保留原文，便于回查 `SKILL.md`。
4. 写到 `docs/skill-guides/<source>--<name>.md`，覆盖已存在的文件。

**完成标准**：文件存在，正文正好 8 个 `##` 节，`## 8. 出处` 里的 commit 与 catalog 一致，内容是对原文的重述而非照搬。

## 批量制作流程

用户要求批量或"全部"时：

1. 读 `catalog/catalog.json`，取 `skills` 数组里的全部 id，按来源顺序处理：`my` → `mattpocock` → `academic` → `anthropic`（各来源内部按 `id` 字母序）。
2. 对每个 skill 执行「单一制作流程」的四步。
3. 全部写完后校验：`docs/skill-guides/` 下的 `.md` 文件数与 catalog 的 skill 数一致，且每个 catalog id 都有对应的 `<source>--<name>.md`。

**完成标准**：catalog 里每个 skill 都有对应说明文件，无缺失、无多余，每篇正好 8 个 `##` 节。

## 关键原则

- **重述，不照搬**：用自己的话讲透 skill 的内在逻辑，不复现原文的步骤编号和代码。照搬等于让读者再读一遍原文，没有增量。风险是失真——所以 `## 8. 出处` 保留路径和 commit 供回查。
- **中文优先**：讲解全中文，英文术语、标题、命令、代码、示例保留原文。
- **核心心智模型是分水岭**：每个 skill 都有一两个"懂了它其余顺理成章"的概念。把 `## 3` 抓准，全篇就有灵魂；抓不准，其余只是信息罗列。
- **先读全再写**：不读 `SKILL.md` 全文就动笔，等于凭 description 猜，产出会失真。
- **同名冲突要标注**：`pdf`、`xlsx` 各有 `academic` 和 `anthropic` 两个实现，在 `## 6` 里标注"与 X 同名冲突"。
- **占位模板特殊处理**：`anthropic/template-skill` 是占位模板，写一篇说明"它是模板、用于复制出新 skill"的最小说明即可，不必硬套完整 8 节深度。

## 边界

- **不建总索引**：不做 `README.md` 路由表，说明文档是一篇一篇的深度说明，路由不是目的。
- **不写机器稿**：不生成"证据目录"（文件夹地图、附属文件清单、函数名/配置字段扫描），那是旧脚本的做法。
- **不照搬、不做逐段翻译**：`## 4` 和全文都是重述，不是原文翻译。
- **不读代码实现、只读 SKILL.md 正文**：说明文档理解的是 skill 的作用与心智模型，不是它的实现细节。
