# seaborn

> 统计可视化（pandas 集成）：箱线图、小提琴图、成对图、热力图，用最少的代码出好看的统计图。

## 1. 一句话理解

`seaborn` 是**统计绘图的高层库**：直接面向 DataFrame 和命名变量，自动做统计估计（聚合、误差、置信区间），用最少的代码出出版级统计图。

## 2. 它解决什么问题

matplotlib 要手写聚合、误差棒、置信区间，代码冗长。seaborn 把"统计语义"内置——给 DataFrame + 变量名，自动映射颜色/大小/样式、自动算统计量。

## 3. 核心心智模型

**设计哲学五条**：面向数据集（直接用 DataFrame 与命名变量，而非抽象坐标）；语义映射（数据值自动变视觉属性）；统计感知（内置聚合/误差/置信区间）；审美默认（出版级主题与调色板开箱即用）；matplotlib 集成（需要时完全可定制）。

**接口两套**：函数接口（传统）与对象接口（现代，声明式）。适合箱线图、小提琴图、成对图、热力图。

## 4. 一次典型运转

`sns.load_dataset` 载入 → `sns.scatterplot(data, x, y, hue)` 一条出图 → 需要再落到 matplotlib 细调。

## 5. 何时用 / 何时不用

**用**：快速探索分布、关系、分类比较，箱线图/小提琴图/成对图/热力图，要漂亮默认值。

**不用**：需要全定制（`matplotlib`）；出版级多面板期刊图（`scientific-visualization`）；交互图（`plotly`）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 基于 matplotlib。

## 7. 易错点与坑

- **data 与 x/y 传参混用**：要面向 DataFrame 用 `data=df, x=..., y=...`，别传裸数组失去统计语义。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/seaborn/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
