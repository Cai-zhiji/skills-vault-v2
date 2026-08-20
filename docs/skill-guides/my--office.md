# office

> 处理 Word（`.docx`）、Excel（`.xlsx`）、PowerPoint（`.pptx`）：所有创建、读取、编辑、分析 Office 文档的操作，都必须通过 `officecli` 完成。

## 1. 一句话理解

`office` 是一条**强制纪律**：Office 文档的一切读写都走 `officecli`（一个 CLI 工具），禁止用 python-docx / openpyxl / python-pptx 这些第三方库。它把"路径 + 命令 + 属性"这套操作语法固化成一份速查，其中 GB/T 9704 公文排版是它的核心场景。

## 2. 它解决什么问题

直接操作 Office 二进制格式很啰嗦、易错，而 Python 生态的三方库（python-docx/openpyxl/python-pptx）各有各的坑、API 不统一、还常遇到中文排版难题。`officecli` 把它们统一成一条命令路径：`view`（读）、`get`/`query`（查）、`add`/`set`/`remove`/`move`/`swap`（改）、`batch`（批量）、`validate`/`dump`/`raw`（校验与兜底）。skill 的价值在于把这些命令的**正确用法和最容易踩的坑**（引号、batch、字体、缩进单位）提前写死。

## 3. 核心心智模型

**文档是一棵可以按路径寻址的树。** 所有操作都围绕一条形如 `/body/p[1]` 或 `/body/table[1]/row[1]/cell[1]` 的路径展开。理解了这一点，`get`/`set`/`add`/`remove` 就都是同一件事：定位一个节点，然后读它、改它、增删它。

三个反复出现的约定：

- **路径含 `[brackets]` 必须加引号**——Shell 会把 `[1]` 当 glob 展开，`/body/p[1]` 不加引号就报 `no matches found`。这是**最高频报错源**。
- **`batch` 优先**——多步操作（建文档 + 设页边距 + 加段落）用 `batch` 一次做完，比逐条 CLI 快且可靠；但 `create` 必须单独执行，不能放进 batch。
- **Schema 用 `help` 发现**——不确定属性名就 `officecli help docx paragraph` 之类，别猜。

## 4. 一次典型运转

生成一份 GB/T 9704 公文（"关于XX的请示"）：

1. `officecli create 公文.docx`（单独执行）
2. `officecli batch 公文.docx --commands '[...]'`：第一条 `set` 设页边距（上3.7/下3.5/左2.8/右2.6cm）+ `docDefaults`（仿宋 16pt），后面 `add` 标题（方正小标宋 22pt 加粗居中）、主送机关（顶格）、正文（仿宋 16pt，`lineSpacing=28pt`、`lineRule=exact`、`firstLineIndent=32pt`）。
3. `officecli validate 公文.docx` 过 OpenXML schema 校验。
4. 需要预览就 `officecli view 公文.docx screenshot` 或 `watch` 浏览器实时预览。

## 5. 何时用 / 何时不用

**用**：任何 `.docx`/`.xlsx`/`.pptx` 的创建、读取、编辑、分析——报告、公文、表格、幻灯片、模板合并（`merge` 做 `{{key}}` 替换）。

**不用**：PDF（用 `pdf` 类技能）、纯文本、HTML 报告等非 Office 产物。也不用（更准确说是**禁止用**）python-docx/openpyxl/python-pptx——这是硬规则。

## 6. 依赖与网络位置

- 依赖 `officecli` 命令行工具（CLI，经 `Bash` 调用）。
- 支持驻留模式（`open`/`save`/`close`）与 `OFFICECLI_RESIDENT_FLUSH` 环境变量控制刷写。
- 与 `cloudbase`/`miniprogram-dev` 无依赖关系；是 `my` 来源里独立的文档处理工具。

## 7. 易错点与坑

- **`no matches found: /body/p[1]`** → 路径没加引号。
- **中文字体不生效** → 只设了 `font.latin` 没设 `font.ea`；用 `font`（同时设两个槽）或显式加 `font.ea`。
- **`firstLineIndent=2char` 不生效** → 只支持绝对数值，改 `"32pt"`。
- **`size` 不是 `fontSize`** → 属性名是 `size`。
- **batch 报 `File not found`** → `create` 被放进了 batch；必须单独执行。
- **外部程序（Word/WPS）看不到最新修改** → 驻留模式下没 `save`/`close` 刷写。
- **每个 add paragraph 必须显式 `font`** → 否则回落 docDefaults（Times New Roman），中文变默认字体。
- **表格 `data` 格式**：逗号分列、分号分行，第一行表头，别留多余空格。

## 8. 出处

- 原始路径：`my-skills/office/SKILL.md`
- 附属：无（单文件 SKILL.md）
- 平台兼容：codex、claude（both）
