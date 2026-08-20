# pdf (anthropic)

> PDF 全流程：读取/提取文本表格、合并/拆分、旋转、水印、新建、填表、加解密、提取图片、OCR 扫描件。

## 1. 一句话理解

`pdf` 是**PDF 处理指南**：用 pypdf / pdfplumber / reportlab 等 Python 库做读取、提取、合并、拆分、生成、加解密全套操作。高级特性在 `REFERENCE.md`，填表先读 `FORMS.md`。

## 2. 它解决什么问题

PDF 是"只能看不好改"的格式，但经常要提取文本/表、合并拆分、填表、OCR。本 skill 按操作分库，给即用代码。

## 3. 核心心智模型

**按库分工**：pypdf（基础：合并/拆分/旋转/加解密/提取）、pdfplumber（文本与表格提取）、reportlab（创建新 PDF）。填表走 `FORMS.md`，高级/JS 库走 `REFERENCE.md`。

## 4. 一次典型运转

`PdfReader` 读 → 提取文本/表 → 需要就合并/拆分/水印 → 或 `reportlab` 生成 → OCR 扫描件。

## 5. 何时用 / 何时不用

**用**：任何 PDF 相关操作（读/提取/合并/拆分/旋转/水印/新建/填表/加解密/提图/OCR）。

**不用**：非 PDF 文件。

## 6. 依赖与网络位置

- 是 `anthropic` 来源的技能。
- **与 `academic/pdf` 同名冲突**——两个实现，最终只能启用一个。

## 7. 易错点与坑

- **填表用错流程**：先读 `FORMS.md`。
- **提取表格用错库**：表格提取优先 pdfplumber。
- **能直接提取就别 OCR**。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/pdf/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
