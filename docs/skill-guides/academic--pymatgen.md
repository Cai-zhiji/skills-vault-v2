# pymatgen

> 材料科学工具：晶体结构（CIF/POSCAR）、相图、能带、态密度、Materials Project 集成、格式转换。

## 1. 一句话理解

`pymatgen`（Python Materials Genomics）是**计算材料科学的核心库**，支撑 Materials Project：创建、分析、操作晶体结构与分子，算相图与热力学性质，分析电子结构（能带、DOS），生成表面/界面，访问 Materials Project 数据库。

## 2. 它解决什么问题

材料计算要处理晶体结构（CIF/POSCAR/XYZ 等 100+ 格式）、对称性、空间群、能带、态密度、相图，还要对接 VASP/Gaussian/Quantum ESPRESSO 等计算代码的输出。`pymatgen` 把这些统一起来。

## 3. 核心心智模型

**结构对象 + 分析器 + 数据库。** 能力分块：从文件读结构（自动识别格式）、结构与对称性分析、相图与热力学稳定、电子结构（带隙/DOS/能带）、表面与界面、Materials Project API 访问、高通量工作流。

## 4. 一次典型运转

从 CIF/POSCAR 读结构 → 分析对称性/空间群 → 算相图或热力学稳定 → 分析能带/DOS → 或对接 Materials Project API。

## 5. 何时用 / 何时不用

**用**：材料科学晶体/分子结构、格式转换、对称性分析、相图/热力学、电子结构、表面/界面、Materials Project、高通量计算、对接 VASP/Gaussian/QE 等。

**不用**：非材料计算场景。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 可选依赖扩展功能；Materials Project API 需 key。

## 7. 易错点与坑

- **格式识别靠文件内容**：pymatgen 自动识别，但确认读入结构是否正确（元素/晶格/坐标）。
- **Materials Project 需 API key**：不擅自动用，除非任务需要且用户同意。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/pymatgen/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
