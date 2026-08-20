# xlsx (anthropic)

> 电子表格全流程：创建、读取、编辑 `.xlsx`/`.xlsm`/`.xltx`/`.csv`/`.tsv`，公式、格式化、图表、清洗。

## 1. 一句话理解

`xlsx` 是**电子表格工具**：按任务选方法——创建/编辑用 openpyxl，批量数据用 pandas，快速查看用 markitdown，读模型（公式+值）用两次 `load_workbook`。

## 2. 它解决什么问题

表格数据的创建/编辑/清洗/公式有很多坑（公式无缓存值、模板格式、财务模型配色）。本 skill 给方法选型 + 硬性输出要求 + `recalc.py` 重算公式。

## 3. 核心心智模型

**按任务选方法**：

| 任务 | 方法 |
| --- | --- |
| 创建/编辑（公式/格式） | openpyxl |
| 批量数据进出 | pandas |
| 快速看 | markitdown（每 sheet 一节，无单元格坐标，别据此规划编辑） |
| 读模型（公式+值） | 两次 `load_workbook` |

**每次输出的硬要求**：专业字体（Arial/Times New Roman）；**零公式错误**（`recalc.py` 报 errors 就不发）；**用公式不硬编码结果**（`=SUM(B2:B9)` 而非算好的总数，让表在输入变化时重算）；**逐字遵循用户 spec**（确切 tab 名、列头、公式）；**记录每个假设和硬编码数字**（单元格批注或相邻格，有真实来源就引用）；**给"给人填的表"加图例 + 一行示例值**（但别给"让你编辑的已有文件"加）；**编辑已有文件精确匹配其约定**（约定优先于这些指南）。

**重算（含公式就必须跑）**：openpyxl 写公式字符串**无缓存值**，不重算则所有公式格读成 `None`——`python scripts/recalc.py output.xlsx`。

## 4. 一次典型运转

openpyxl 写公式 → `recalc.py` 重算 → 校验零公式错误 → 需要就 pandas 批量进出。

## 5. 何时用 / 何时不用

**用**：开/读/改/修 `.xlsx`/`.xlsm`/`.xltx`/`.csv`/`.tsv`、建新表、格式转换、清洗脏数据。

**不用**：主要交付是 Word/HTML/Python 脚本/DB pipeline/Google Sheets API（哪怕有表格数据）。

## 6. 依赖与网络位置

- 依赖 openpyxl、pandas、markitdown（预装）。
- 附属：`scripts/recalc.py`。
- **与 `academic/xlsx` 同名冲突**——两个实现，最终只能启用一个。

## 7. 易错点与坑

- **忘 `recalc.py`**：不重算，公式格全读成 `None`。
- **硬编码结果而非公式**：表必须能随输入重算。
- **编辑已有文件强加标准格式**：约定优先，找既有输入格只写那里。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/xlsx/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
