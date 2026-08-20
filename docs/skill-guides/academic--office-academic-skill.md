# office-academic-skill

> 中文优先的学术 Word/PPT 工作流：论文阅读报告、毕业论文或组会 PPT、可编辑 DOCX/PPTX 生成、Office 文件检查、模板匹配、演讲者备注与排版质检。

## 1. 一句话理解

`office-academic-skill` 负责**学术场景的 Office 产出**：把论文/毕业论文/数据转成 Word 报告或 PPT，并保证"可编辑、可检查、中文优先、保留英文术语"。它的边界很清晰——只要最终交付物是 Word/PPT，就归它。

## 2. 它解决什么问题

学术汇报（文献报告、组会、开题/中期/答辩、课程报告）的产出是高频且格式敏感的工作：既要中文表达，又要保留英文题名、公式、变量、命令、参考文献；既要有证据，又不能编造 DOI/作者/期刊/数值。本 skill 把"中文优先 + 证据标注 + 可编辑 + 质量门"钉成一条流程。

## 3. 核心心智模型

**证据标注（evidence label）是灵魂。** 所有输出要区分五类来源：`论文原文` / `图表/公式证据` / `代码或仿真结果` / `根据上下文推断` / `建议`。绝不编造 DOI、作者、期刊、实验值、图号、章节名、页码、结论；对主张、参数、定量结果、公式解释、数据集、图、局限、创新点都贴来源标签。

**两条分工边界**：纯论文正文（无 Word/PPT 交付物）→ `research-writing-skill`；MATLAB/Python 分析/统计/绘图（除非要插进 Word/PPT）→ `scientific-toolkit-skill`。

**PPT 的两个固定结构**：研究型 PPT 九节（封面→背景→相关工作/理论→方法→实验→结果→对比讨论→贡献/局限/展望→Q&A）；论文阅读型 PPT 十节（元数据→背景→核心问题→方法框架→实验→主要结果→贡献→局限→改进→与你课题的关系）。

## 4. 一次典型运转

做一份"论文阅读 Word 报告"：

1. 默认产出双语（英中）报告 + 中文报告（除非用户另说）。
2. 写前建 source map：标题/作者/venue/年份/DOI、章节与页码跨度、支撑关键主张的图表公式数据集、软硬件与评估设置；缺失的标 `未在原文中明确给出`。
3. 用 `references/report-structure.md` 的默认结构 + 证据标签格式写。
4. 生成 `.docx`：结构化标题、汇总表、图表占位、来源标签；中文用微软雅黑/宋体，英文数字用 Times New Roman/Calibri/Arial。
5. 质量门：检查抽取文本/包 XML 有无缺字、中文乱码、坏图、表格溢出、来源标签。

## 5. 何时用 / 何时不用

**用**：读论文写 Word 报告、做/打磨 PPT、把论文/毕业论文材料转幻灯片、编辑 DOCX/PPTX、检查 Office 文件、产出中文学术汇报。

**不用**：纯论文正文（`research-writing-skill`）；MATLAB/Python 分析统计绘图本身（`scientific-toolkit-skill`）。

## 6. 依赖与网络位置

- 与 `research-writing-skill`、`scientific-toolkit-skill` 三足分工。
- 附属：`references/report-structure.md`、`references/office-docx/`（ooxml/docx-js/脚本）、`references/office-pptx/`、`references/thesis-defense-pptx/scripts/`。
- 曾审阅 `academic-pptx` 仓库，因其专有许可，只取通用原则不复制文本。

## 7. 易错点与坑

- **编造文献细节**：DOI/作者/期刊/数值/图号/页码一律不得捏造。
- **直接改用户原始 PPTX**：要在时间戳/版本副本上工作。
- **禁用 PowerPoint 加载项或改应用设置**：未经用户明确批准不做。
- **长段落堆砌**：一页一个核心点，用动作式标题（陈述结论），图表公式承载论证。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/office-academic-skill/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
