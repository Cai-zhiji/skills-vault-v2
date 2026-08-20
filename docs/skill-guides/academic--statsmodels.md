# statsmodels

> 统计模型库：OLS/GLM/混合模型/ARIMA，带详细诊断、残差、推断与系数表。

## 1. 一句话理解

`statsmodels` 是 Python 的**统计建模与计量经济学**库：从线性回归到时间序列到计量分析，提供估计、推断、诊断，产出带系数表、残差、显著性检验的严谨结果。

## 2. 它解决什么问题

需要"严格推断"的场景——OLS/GLM/混合模型/ARIMA 这类具体模型类，要系数表、诊断、残差分析、假设检验（异方差/自相关/正态性）、离群点检测。scikit-learn 偏预测，statsmodels 偏推断。

## 3. 核心心智模型

**推断优先于预测。** 核心能力：回归（OLS/WLS/GLS/分位数）、广义线性模型（logistic/Poisson/Gamma）、离散结果（二元/多项/计数/序数）、时间序列（ARIMA/SARIMAX/VAR/预测）、统计检验与诊断、模型假设检验、离群点/影响点检测、模型比较（AIC/BIC/似然比）、因果效应估计、出版级统计表。

**OLS 一个固定坑**：跑 OLS 前**必须**加常数项（`sm.add_constant(X)`）。

## 4. 一次典型运转

`add_constant` → 拟合 OLS → `model.summary()` 看完整结果（系数/p 值/R²/诊断）→ 带置信区间的预测。

## 5. 何时用 / 何时不用

**用**：OLS/GLM/混合模型/ARIMA、时间序列、统计检验诊断、模型假设检验、离群点、模型比较、因果估计、出版级统计表。

**不用**：引导式选检验 + APA 报告（`statistical-analysis`）；纯预测 ML（`scikit-learn`）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 与 `statistical-analysis` 互补。

## 7. 易错点与坑

- **OLS 忘加常数**：必须 `sm.add_constant(X)`，否则截距缺失、结果错。
- **拿推断结果当预测**：statsmodels 强在推断，预测场景用 scikit-learn。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/statsmodels/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
