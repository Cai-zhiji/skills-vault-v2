# scientific-visualization

> 出版级配图 meta-skill：多面板、显著性标注、误差棒、色盲安全配色、期刊格式（Nature/Science/Cell）。

## 1. 一句话理解

`scientific-visualization` 是**出版级图的"总调度"**：它不替代 matplotlib/seaborn/plotly，而是编排它们做出符合期刊投稿要求的图——多面板统一风格、误差棒、显著性标注、色盲安全配色、正确的分辨率与格式。

## 2. 它解决什么问题

期刊投稿的图有硬要求：多面板布局一致、误差棒、显著性标记、色盲友好、既能在彩色也能在灰度用、特定期刊格式（Nature/Science/Cell/PLOS）、正确分辨率与格式（PDF/EPS/TIFF）。散着用 matplotlib 很难一次达标，本 skill 把"出版标准"固化成流程。

## 3. 核心心智模型

**出版样式预设 + 多面板 + 无障碍配色。** 用 `scripts/style_presets.py` 的 `apply_publication_style('default')` 套出版样式，再按期刊要求做多面板、误差棒、显著性标注、色盲安全调色板，导出 PDF/EPS/TIFF。快速探索用 `seaborn`/`plotly`，出图用本 skill。

## 4. 一次典型运转

套出版样式 → 建多面板图 → 加误差棒/显著性标注 → 用色盲安全配色 → 按期刊导出正确分辨率与格式。

## 5. 何时用 / 何时不用

**用**：投期刊的图、多面板统一风格、色盲友好/无障碍、正确分辨率格式、遵循特定出版指南、提升已有图到出版标准、需彩色+灰度双用。

**不用**：快速探索图（直接 `seaborn`/`plotly`）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 编排 matplotlib/seaborn/plotly；附属 `scripts/style_presets.py`。

## 7. 易错点与坑

- **色盲不友好配色**：期刊要求，用安全调色板。
- **分辨率/格式不对**：按期刊要求 PDF/EPS/TIFF，别给 PNG 低清。
- **多面板风格不一致**：用统一出版样式，别每张图各搞一套。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/scientific-visualization/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
