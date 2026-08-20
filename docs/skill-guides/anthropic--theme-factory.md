# theme-factory

> 用主题给产物套样式：10 套预设配色+字体主题，可应用到幻灯片、文档、报告、落地页。

## 1. 一句话理解

`theme-factory` 是一个**主题库**：10 套精心挑选的专业字体+配色主题（Ocean Depths、Sunset Boulevard、Modern Minimalist…），选定一套就能应用到任意产物，或临时生成新主题。

## 2. 它解决什么问题

给幻灯片/文档/报告/落地页套一致的视觉主题，靠手挑配色+字体既慢又不专业。本 skill 提供现成的、各配 hex 色板和 header/body 字体配对的 10 套主题。

## 3. 核心心智模型

**展示 → 选择 → 应用。** 流程四步：展示 `theme-showcase.pdf`（只看不改）→ 问用户选哪套 → 等明确确认 → 把选中主题的色与字体应用到产物。

## 4. 一次典型运转

展示 theme-showcase.pdf → 用户选一套 → 应用该主题的 colors + fonts 到 deck/artifact。

## 5. 何时用 / 何时不用

**用**：给幻灯片、文档、报告、HTML 落地页等产物套主题。

**不用**：需要完全自定义、无预设主题的场景（可临时生成新主题）。

## 6. 依赖与网络位置

- 附属 `theme-showcase.pdf`。
- 是 `anthropic` 来源的样式工具。

## 7. 易错点与坑

- **未确认就应用**：要等用户明确选哪套再套。
- **修改 showcase**：theme-showcase.pdf 只展示，不改。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/theme-factory/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
