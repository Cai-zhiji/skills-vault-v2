# scientific-toolkit-skill

> 面向光电信息科学与工程的科研计算工具箱：MATLAB/Octave、Python 科学分析、信号/图像处理、统计、仿真、优化、出版级图表、传感/时间序列数据、文献检索与常用科学库。

## 1. 一句话理解

`scientific-toolkit-skill` 是科研**计算**的总入口：只要任务本质是 MATLAB/Python/绘图/统计/仿真/优化/文献检索（而不是写论文正文、也不是做 Word/PPT），就归它。它自身很薄，真正的细节挂在下面 20 来个 `references/scientific-skills/` 子技能上。

## 2. 它解决什么问题

科研计算的需求高度分散——今天做 FFT 去噪、明天做多目标优化、后天查文献。本 skill 提供一个**按需路由**的伞：识别你手里是什么活，指向对应的子技能（matplotlib/seaborn 绘图、statsmodels 统计、scikit-learn 机器学习、sympy 符号、pymoo 优化、simpy 仿真、qutip 量子、pymatgen 材料、astropy 天文、xlsx/pdf 工具……），只加载需要的那个 reference。

## 3. 核心心智模型

**领域锚定 + 按需加载。** 用户领域固定为光电信息科学与工程，示例和检查默认贴近：光学、光电子、光通信、光纤传感（BOTDR/BOTDA、BGS）、SPM、色散、噪声、反卷积、信号/图像处理、光谱、探测器数据、传感时间序列、标定与不确定度。

**两条硬纪律**：

- **不编造**物理参数、材料常数、软件菜单操作、实验数据、论文结论；不确定就问源文件或标注假设。
- **不擅自装包/调云 API/外发数据**：一些子技能提 `uv pip install` 或可选 API key，除非任务确需且用户同意，否则不装、不调、不传。

**两条分工边界**：论文正文 → `research-writing-skill`；Word/PPT → `office-academic-skill`。

## 4. 一次典型运转

用户要"对一组传感时序做去噪并出出版级图"：

1. 读已有代码/数据/README 再动。
2. 识别变量/维度/单位/路径/随机种子/期望图。
3. 路由到 `matplotlib`（或 `scientific-visualization` 出期刊图）+ `statistical-analysis`/`statsmodels`。
4. 小步可验证改动，优先成熟库；加 `rng` 保证随机可复现；关键参数集中、避免硬编码绝对路径。
5. 跑脚本级验证，出高分辨率 `.png` + 矢量 `.svg`。
6. 报告环境、命令、输出路径、生成的图、已知局限。

## 5. 何时用 / 何时不用

**用**：要 MATLAB 代码、科学 Python、数据分析、绘图、仿真、公式、统计、机器学习、光学/物理/材料计算、可复现科研工作流时。

**不用**：写论文正文（`research-writing-skill`）；做 Word/PPT（`office-academic-skill`）。

## 6. 依赖与网络位置

- 是 `academic` 来源的伞，下挂 21 个 `references/scientific-skills/` 子技能（全部是 embedded 分类）。
- 与另两个学术 skill 三足分工。

## 7. 易错点与坑

- **泄露/提交密钥或未发表内容**：API key、token、私有数据、未发表论文内容都不得暴露。
- **覆盖原始数据/代码/图**：写版本化输出，不覆盖原件。
- **未经确认递归清理用户文件**：禁止。
- **把本地推断当实时查询结果**：外部检索要区分"实时查询结果"和"本地推断"。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
