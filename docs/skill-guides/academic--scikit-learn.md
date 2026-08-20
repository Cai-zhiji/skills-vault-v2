# scikit-learn

> Python 机器学习：分类、回归、聚类、降维、预处理、模型评估、超参调优、pipeline。

## 1. 一句话理解

`scikit-learn` 是**经典机器学习的事实标准**：监督（分类/回归）、非监督（聚类/降维）、模型评估、超参调优、预处理、生产级 ML pipeline 的完整参考。

## 2. 它解决什么问题

经典 ML（非深度学习）的绝大多数任务——训练、评估、调参、部署 pipeline——用 scikit-learn 一套搞定，且 API 高度统一（`fit`/`predict`/`transform`）。

## 3. 核心心智模型

**统一 API**：estimator 都有 `fit`/`predict`（或 `transform`），`Pipeline` 把预处理 + 模型串成一条。能力分块：分类、回归、聚类、降维、预处理与数据变换、交叉验证评估、超参（grid/random search）、pipeline、多算法对比。

## 4. 一次典型运转

切分数据 → 预处理（标准化/编码）→ 选模型 → 交叉验证评估 → 调超参 → 组装 pipeline → 预测。

## 5. 何时用 / 何时不用

**用**：分类/回归、聚类/降维、预处理、交叉验证评估、超参调优、ML pipeline、多算法对比。

**不用**：深度学习（用 PyTorch/TF）；纯统计推断（`statsmodels`）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 常配 matplotlib/seaborn（可视化）、pandas/numpy。

## 7. 易错点与坑

- **数据泄漏**：预处理要在训练集上 fit、再 transform 测试集（放进 pipeline 避免泄漏）。
- **指标选错**：分类/回归各有适用指标，别拿准确率衡量不平衡数据。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/scikit-learn/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
