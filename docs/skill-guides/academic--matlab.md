# matlab

> MATLAB 与 GNU Octave 数值计算：矩阵运算、数据分析、可视化、科学计算，可交叉转换 MATLAB/Python。

## 1. 一句话理解

`matlab` 覆盖 MATLAB（商业）和 GNU Octave（免费开源、高兼容）两套数值计算环境：矩阵运算、线性代数、信号/图像处理、微分方程、优化、统计、科学可视化。

## 2. 它解决什么问题

光电信息、信号处理等领域大量既有工作用 MATLAB。本 skill 提供 MATLAB/Octave 脚本的写法、语法、调试，以及 MATLAB 与 Python 之间的代码转换；脚本可跑在 MATLAB 或开源 Octave 上（后者无需商业许可）。

## 3. 核心心智模型

**矩阵是核心抽象。** 一切围绕矩阵运算展开。两个运行入口：

- MATLAB（商业）：`matlab -nodisplay -nosplash -r "run('script.m'); exit;"`
- GNU Octave（免费）：`octave script.m`

能力分块：矩阵运算、线性代数、信号处理、图像处理、微分方程、优化、统计、可视化。

## 4. 一次典型运转

写一个 FFT 去噪脚本 → 用 Octave 本地跑通验证 → 按需转成 MATLAB 或 Python → 出图导出。

## 5. 何时用 / 何时不用

**用**：写 MATLAB/Octave 脚本做线性代数、信号/图像处理、微分方程、优化、统计、科学可视化；需要 MATLAB 语法帮助或 MATLAB↔Python 转换。

**不用**：纯 Python 科学计算（用 NumPy/SciPy 那批子技能）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 运行需装 MATLAB 或 Octave（仅生成脚本则不需要）。

## 7. 易错点与坑

- **硬编码绝对路径**：要集中参数、避免绝对路径。
- **随机仿真不设 `rng`**：需可复现时加 `rng`。
- **MATLAB 与 Octave 语法差异**：转换时注意两者兼容性边界。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/matlab/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
