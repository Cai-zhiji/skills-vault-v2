# matplotlib

> Python 基础绘图库：创建静态/动画/交互图，精细控制每个图形元素，导出 PNG/PDF/SVG。

## 1. 一句话理解

`matplotlib` 是 Python 可视化的**地基**：底层、可全定制，覆盖 pyplot（MATLAB 风格）和面向对象 API（Figure/Axes）两套接口，适合需要精细控制每个图形元素、或做新颖图型时。

## 2. 它解决什么问题

当 seaborn 的默认样式不够、或要精确控制每个元素、或要嵌进特定科学工作流时，需要 matplotlib 这种底层库。它给的是"完全控制权"，代价是代码量。

## 3. 核心心智模型

**对象层级**：`Figure`（顶层容器）→ `Axes`（绘图区）→ `Artist`（线、点、文字等）。两套接口——`pyplot`（快速、MATLAB 风）与 OO 接口（Figure/Axes，可维护、适合复杂图）。

**选型**：快速统计图用 `seaborn`；交互图用 `plotly`；出版级多面板期刊图用 `scientific-visualization`。matplotlib 是它们的底层。

## 4. 一次典型运转

建 Figure/Axes → 画数据 → 设坐标轴/单位/图例/标签 → 导出 PNG/PDF/SVG。

## 5. 何时用 / 何时不用

**用**：任何图（线/散点/柱/直方/热图/等高线）、科学统计可视化、多面板 subplot、导出多种格式、交互/动画、3D、嵌 Jupyter/GUI。

**不用**：想要最少的代码出好看的统计图（`seaborn`）；出版级期刊多面板图（`scientific-visualization`）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 是 `seaborn` 的底层依赖。

## 7. 易错点与坑

- **pyplot 与 OO 混用**：复杂图优先 OO 接口，避免状态混乱。
- **出版图忘了设分辨率/格式**：导出高分辨率 `.png` + 矢量 `.svg`。
- **坐标轴缺单位/图例**：科学图必须带单位、图例、坐标标签。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/matplotlib/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
