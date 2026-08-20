# statistical-analysis

> 引导式统计分析：检验选择、假设检验、功效分析、APA 格式结果，面向学术研究。

## 1. 一句话理解

`statistical-analysis` 是**统计的"向导"**：帮你选对的检验、查假设、做功效分析、用 APA 格式报告结果。它关心的是"该怎么分析、怎么报告"，而不是具体模型实现。

## 2. 它解决什么问题

学术研究里选错检验、漏查假设、报告格式不合规是常见错误。本 skill 提供从检验选择到 APA 报告的完整引导。

## 3. 核心心智模型

**能力五块**：检验选择与规划（按研究问题与数据选检验，先验功效分析定样本量，多重比较校正）；假设检验（跑前自动核验所有假设，给 Q-Q 图/残差图/箱线图诊断）；统计检验（t 检验/ANOVA/卡方/回归/相关/贝叶斯）；效应量与解释；专业报告（APA 格式）。

**选型分工**：要"引导选检验 + APA 报告"用本 skill；要"具体模型类实现"用 `statsmodels`。

## 4. 一次典型运转

明确研究问题 → 选检验 → 查假设（诊断图）→ 跑检验 → 算效应量 → APA 格式报告。

## 5. 何时用 / 何时不用

**用**：选检验、假设检查、功效分析、APA 报告、分析实验/观测数据。

**不用**：要实现具体模型（OLS/GLM/ARIMA）→ `statsmodels`。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 与 `statsmodels` 互补（引导 vs 实现）。

## 7. 易错点与坑

- **不查假设就跑检验**：假设违反（如非正态）会得出错结论。
- **报告不用 APA**：学术报告要合规。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/statistical-analysis/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
