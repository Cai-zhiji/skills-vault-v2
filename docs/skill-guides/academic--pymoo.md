# pymoo

> 多目标优化框架：NSGA-II/III、MOEA/D、Pareto 前沿、约束处理、基准问题（ZDT/DTLZ）。

## 1. 一句话理解

`pymoo` 是**多目标优化的 Python 框架**：用 NSGA-II/III、MOEA/D 等进化算法解单/多目标优化，擅长找冲突目标之间的权衡解（Pareto 前沿）。

## 2. 它解决什么问题

工程优化里多个目标常互相冲突（性能 vs 成本 vs 尺寸），不存在单一最优，只有一堆权衡解。`pymoo` 用进化算法找出 Pareto 前沿，让人在解之间做多准则决策。

## 3. 核心心智模型

**统一接口 `minimize()`。** 所有优化任务都走同一个 `minimize()` 函数，只换 problem / algorithm / termination 配置。能力分块：单/多目标优化、进化算法（GA/DE/PSO/NSGA-II/III）、约束优化、基准问题（ZDT/DTLZ/WFG）、自定义遗传算子、高维结果可视化、多准则决策、离散/连续/混合变量。

## 4. 一次典型运转

定义 problem（目标 + 约束）→ 选算法（NSGA-II）→ 配 termination → `minimize()` → 可视化 Pareto 前沿 → 多准则决策。

## 5. 何时用 / 何时不用

**用**：单/多目标优化、找 Pareto 解、进化算法、约束优化、基准测试、可视化高维结果、多解决策。

**不用**：单目标且可用梯度法快速求解的（用 SciPy optimize 更轻）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。

## 7. 易错点与坑

- **目标和约束写错方向**：多目标要明确"最小化还是最大化"，约束要规范成 `g <= 0`。
- **忽略 Pareto 前沿的多样性**：NSGA-II 靠 crowding distance 维持多样性，别只看收敛。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/pymoo/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
