# exploratory-data-analysis

> 对科学数据文件做探索性数据分析（EDA）：自动识别 200+ 文件格式、格式专属分析、质量评估、生成详细 Markdown 报告。

## 1. 一句话理解

`exploratory-data-analysis` 是一个**数据体检工具**：丢给它一个科学数据文件，它自动识别文件类型，做格式专属的分析、数据质量评估、统计摘要与分布，产出适合存档和规划后续分析的 Markdown 报告。

## 2. 它解决什么问题

科研数据格式极多（化学、生物信息、显微、光谱、蛋白质组、代谢组、通用科学格式），在深入分析前，人需要先搞清楚"这是什么、结构如何、质量怎样、该往哪个方向走"。本 skill 把这一步自动化。

## 3. 核心心智模型

**格式检测驱动。** 核心能力五条：自动检测并分析 200+ 科学格式；格式专属元数据提取；数据质量与完整性评估；统计摘要与分布；可视化建议 + 下游分析建议，最后生成 Markdown 报告。

## 4. 一次典型运转

用户给一个数据文件路径 → 自动检测类型 → 提取元数据 → 质量/完整性评估 → 统计摘要与分布 → 生成 Markdown 报告（含可视化与下游建议）。

## 5. 何时用 / 何时不用

**用**：用户给了一个数据文件要分析、要"explore/analyze/summarize"、要在分析前全面了解数据集。

**不用**：已经明确知道数据结构和要做的具体分析（直接进对应库）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。

## 7. 易错点与坑

- **跳过 EDA 直接建模**：不知道数据结构/质量就分析容易得出错结论。
- **报告不留档**：Markdown 报告是给后续分析和存档的，别只口头汇报。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/exploratory-data-analysis/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
