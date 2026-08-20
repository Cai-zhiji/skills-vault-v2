# pdf (academic)

> PDF 处理：读取/提取文本表格、合并/拆分、旋转、加水印、建新 PDF、填表单、加解密、提取图片、OCR 扫描件。

## 1. 一句话理解

`pdf` 是**PDF 全家桶**：用 pypdf / pdfplumber / reportlab 等 Python 库完成从读取、提取到生成、加解密的全套操作。

## 2. 它解决什么问题

PDF 是"只能看不好改"的格式，但科研里经常要提取文本表格、合并拆分、填表、OCR 扫描件。本 skill 提供按操作分类的库选型与代码。

## 3. 核心心智模型

**按库分工**：

- **pypdf**：基础操作（合并、拆分、旋转、加解密、提取）。
- **pdfplumber**：文本与表格提取（比 pypdf 更强）。
- **reportlab**：创建新 PDF。
- 高级特性、JS 库、详细示例在 `reference.md`；填表先读 `forms.md`。

## 4. 一次典型运转

`PdfReader` 读 → 提取文本/表格 → 需要就合并/拆分/加水印 → 或 `reportlab` 生成新 PDF → OCR 扫描件使其可搜索。

## 5. 何时用 / 何时不用

**用**：任何 PDF 相关操作——读、提取文本/表、合并、拆分、旋转、水印、新建、填表、加解密、提取图、OCR。

**不用**：非 PDF 文件。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- **与 `anthropic/pdf` 同名冲突**——两个实现，最终只能启用一个。

## 7. 易错点与坑

- **填表单用错流程**：先读 `forms.md` 再填。
- **提取表格用错库**：表格提取优先 pdfplumber，不是 pypdf。
- **OCR 扫描件前先确认是否已是文本**：能直接提取就别 OCR。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/pdf/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
