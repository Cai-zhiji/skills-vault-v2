# internal-comms

> 按公司惯用格式撰写内部沟通：3P 更新、公司新闻、FAQ、状态报告、领导层更新、项目更新、事故报告。

## 1. 一句话理解

`internal-comms` 是**内部沟通的模板库**：识别你写的是哪种内部沟通，加载对应的 guideline 文件，按其格式/语气/内容收集规则来写。

## 2. 它解决什么问题

内部沟通（状态报告、领导层更新、3P 更新、公司新闻、FAQ、事故报告）有公司惯用的格式和语气。本 skill 把这些格式固化在 `examples/` 目录里，避免每次现想格式、语气跑偏。

## 3. 核心心智模型

**识别类型 → 加载 guideline → 按规则写。** 三个步骤：

1. 从请求识别沟通类型。
2. 从 `examples/` 加载对应 guideline：`3p-updates.md`（Progress/Plans/Problems）、`company-newsletter.md`、`faq-answers.md`、`general-comms.md`（其余）。
3. 按该文件的格式、语气、内容收集规则写。

不匹配任何现有 guideline 就追问或问清期望格式。

## 4. 一次典型运转

用户要"写周报"→ 识别为 3P 更新 → 加载 `3p-updates.md` → 按其格式（Progress/Plans/Problems）写。

## 5. 何时用 / 何时不用

**用**：写任何内部沟通——状态报告、领导层更新、3P 更新、公司新闻、FAQ、事故报告、项目更新。

**不用**：对外沟通（客户/公众）或纯技术文档。

## 6. 依赖与网络位置

- 附属 `examples/` 目录多个 guideline。
- 是 `anthropic` 来源的写作类技能。

## 7. 易错点与坑

- **套错模板**：先识别类型再加载，别拿 newsletter 模板写事故报告。
- **不匹配硬套**：没有对应 guideline 就追问，别生搬硬套。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/internal-comms/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
