# docx

> Word 文档（`.docx`/`.dotx`）创建、读取、编辑：目录、页眉页脚、批注、修订、find-replace、图片、转换。

## 1. 一句话理解

`docx` 是**Word 文档的全流程工具**：`.docx` 本质是一个 ZIP + XML，按任务选方法——创建用 docx-js 脚本，编辑用 unzip→改 XML→zip，读取用 pandoc。

## 2. 它解决什么问题

Word 文档的格式细节（A4 vs Letter、横版、表格宽度、列表项目符号、目录层级、页码）坑极多。本 skill 把 docx-js 的 footgun 逐条列出（"这些是坑"），并规定"写完必须渲染看一遍"。

## 3. 核心心智模型

**按任务选方法**：

| 任务 | 方法 |
| --- | --- |
| 创建 | 写 docx-js 脚本 |
| 编辑已有 | `unzip` → 改 `word/document.xml` → `zip`（docx-js 打不开已有文件） |
| 读取 | `pandoc -t markdown file.docx` |

**docx-js 的 footgun 清单**：页面默认 A4（US Letter 要显式 DXA 尺寸）；横版传 portrait 尺寸 + `PageOrientation.LANDSCAPE`；表格要 table 和 cell 双重宽度（DXA，PERCENTAGE 在 Google Docs 会坏）；表格底纹用 `ShadingType.CLEAR`（SOLID 渲染成黑）；列表用 `numbering` 不用字面 `•`；`ImageRun` 要 `type`；`PageBreak` 必须在 Paragraph 内；**绝不用 `\n`**（用多个 Paragraph）；目录标题要用内置 `HeadingLevel.*`（自定义样式需 `outlineLevel`）；别用表格当横线；点线对齐用 `PositionalTab`。

## 4. 一次典型运转

写脚本（docx-js）创建 → 注意 footgun（尺寸/表格/列表/目录）→ 渲染看输出 → 需要就改。

## 5. 何时用 / 何时不用

**用**：创建/读/编辑 Word 文档与模板、目录、页眉页脚、批注、修订、find-replace、插图、转成 Word。

**不用**：PDF、电子表格、Google Docs、与文档生成无关的编码任务。

## 6. 依赖与网络位置

- 依赖 docx（npm，预装）、pandoc。
- 与 `pptx`（PowerPoint）、`xlsx`（Excel）是 Office 三件套，同属 `anthropic`。

## 7. 易错点与坑

- **页面默认 A4**：US Letter 要显式设 DXA 尺寸。
- **表格底纹用 SOLID**：会渲染成黑色，用 CLEAR。
- **字面 `•` 和 `\n`**：用 numbering 和多个 Paragraph。
- **目录标题不出现在 TOC**：用内置 HeadingLevel 或设 outlineLevel。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/docx/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
