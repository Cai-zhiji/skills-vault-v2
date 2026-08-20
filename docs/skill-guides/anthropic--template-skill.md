# template-skill

> Skill 模板（占位），用于复制出新 Skill 的起点。

## 1. 一句话理解

`template-skill` 不是真实 skill，而是一个**占位模板**——frontmatter 的 description 是"Replace with description of the skill and when Claude should use it"，正文只有一句"Insert instructions below"。它的作用是让你复制它、填入自己的内容，快速搭一个新 skill 的骨架。

## 2. 它解决什么问题

从零建 skill 时，frontmatter 字段、文件结构这些"脚手架"每次都要重想。模板提供一个标准起点，只需替换 name / description 和正文指令。

## 3. 核心心智模型

**占位符，不是能力。** 它没有可执行的行为——正文就是一个"在这里填指令"的标记。用它的方式不是"调用它"，而是"复制它改掉占位符"。

## 4. 一次典型运转

复制 `template/` 目录 → 改 frontmatter 的 `name` / `description` → 把"Insert instructions below"替换成真正的 skill 指令。

## 5. 何时用 / 何时不用

**用**：要新建一个 skill、需要标准骨架时（复制用）。

**不用**：把它当真正的 skill 去"调用"——它没有可执行内容。

## 6. 依赖与网络位置

- 是 `anthropic` 来源的 `template/`（分类为 template，非 published）。
- 与 `skill-creator`（造 skill 的完整流程）互补——本模板是其中"写 SKILL.md"的起点骨架。

## 7. 易错点与坑

- **把占位符当能力**：直接调用它不会有任何效果。
- **忘改 description**：frontmatter 的 description 决定触发，占位符不换就永远不该触发。

## 8. 出处

- 原始路径：`sources/anthropic-skills/template/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
