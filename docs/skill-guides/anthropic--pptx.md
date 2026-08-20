# pptx

> PowerPoint（`.pptx`/`.potx`）创建、读取、编辑：模板、演讲者备注、批注、布局、组合拆分。

## 1. 一句话理解

`pptx` 是 **PowerPoint 全流程**：`.pptx` 是 ZIP+XML，按任务选方法——创建用 pptxgenjs 脚本，编辑/套模板用 unzip→改 XML→zip，读取用 markitdown。

## 2. 它解决什么问题

PPT 有大量格式坑（画布尺寸、十六进制颜色、透明度/阴影、项目符号、间距）。本 skill 用 `scripts/` 辅助脚本（缩略图、复制幻灯片、清理、校验）+ pptxgenjs 的 footgun 清单，保证产出不损坏、格式正确。

## 3. 核心心智模型

**按任务选方法 + 一套脚本**：

| 任务 | 方法 |
| --- | --- |
| 创建 | 写 pptxgenjs 脚本 |
| 编辑/套模板 | unzip → 改 `ppt/slides/slideN.xml` → zip |
| 读取 | `markitdown`；视觉网格用 `scripts/thumbnail.py` |

**pptxgenjs 的 footgun**：加幻灯片前先设 `pres.layout`（默认 10"×5.625" 不是 13.3"）；**hex 颜色绝不用 `#`、绝不 8 位**（`color: "FF0000"`，`#FF0000` 会损坏文件）；透明度/阴影各自专用字段；pptxgenjs 会**原地变异选项对象**（别跨 add 调用共享一个 shadow/options 对象）；shadow `offset` 必须 ≥0；`letterSpacing` 被忽略（用 `charSpacing`）；列表用 `bullet: true` 而非字面 `•`。

## 4. 一次典型运转

写 pptxgenjs 脚本（先设 layout、注意颜色/阴影/列表 footgun）→ 渲染看输出 → 需要就 `thumbnail.py` 看视觉网格、`validate.py` 校验。

## 5. 何时用 / 何时不用

**用**：任何 `.pptx`/`.potx` 涉及——创建/读取/解析/编辑/组合/拆分/模板/演讲者备注/批注。

**不用**：非 PowerPoint 文件。

## 6. 依赖与网络位置

- 依赖 pptxgenjs（预装）、markitdown。
- 与 `docx`、`xlsx` 是 Office 三件套。
- 附属：`scripts/thumbnail.py`、`add_slide.py`、`clean.py`、`office/validate.py`、`office/soffice.py`。

## 7. 易错点与坑

- **颜色带 `#` 或 8 位**：会损坏文件，用 6 位无 `#`。
- **共享 options 对象**：pptxgenjs 原地变异，每次 add 要新建对象。
- **字面 `•`**：用 `bullet: true`，否则双项目符号。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/pptx/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
