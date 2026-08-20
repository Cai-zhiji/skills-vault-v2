---
name: office
description: 处理 Word (.docx)、Excel (.xlsx)、PowerPoint (.pptx) 文件。所有创建、读取、编辑、分析 Office 文档的操作都必须通过本 skill 调用 officecli 完成。
---

# Office — 文档处理

**强制规则**：所有 `.docx`、`.xlsx`、`.pptx` 文件的创建、读取、编辑、分析，必须使用 officecli，禁止使用 python-docx、openpyxl、python-pptx 等第三方库。

所有 officecli 命令通过 `Bash` 工具以 CLI 方式执行。

---

## 核心原则

### 1. 路径引号 — 最高频报错源

Shell 会把 `[brackets]` 展开为 glob 匹配。所有含方括号的路径**必须用引号包裹**：

```bash
# ❌ 会报错 no matches found
officecli get doc.docx /body/p[1]

# ✅ 正确
officecli get doc.docx "/body/p[1]"
officecli set doc.docx "/body/table[1]/row[1]/cell[1]" --prop text="内容"
```

### 2. batch 优先

多步操作（创建文档、设置页面、添加内容）用 `batch` 一次性完成，比逐条 CLI 调用快得多且更可靠：

```bash
officecli create output.docx
officecli batch output.docx --commands '[
  {"command":"set","path":"/","props":{...}},
  {"command":"add","parent":"/body","type":"paragraph","props":{...}}
]'
```

> `create` 必须单独执行，不能放在 batch 数组内。

### 3. Schema 发现

遇到不确定的属性名、元素类型时，直接用 help 查看：

```bash
officecli help docx              # 列出所有 Word 元素
officecli help docx paragraph    # 查看 paragraph 的全部属性和用法
officecli help docx table        # 查看 table 的全部属性
officecli help all               # 平铺所有格式/元素/属性（可 pipe grep）
```

---

## 读取与查看

```bash
# 内容提取
officecli view <file> text           # 纯文本
officecli view <file> annotated      # 带样式标注的文本
officecli view <file> html           # 渲染为 HTML
officecli view <file> screenshot     # 渲染为 PNG 截图

# 结构探查
officecli view <file> tree           # 树形结构视图（调试首选）
officecli get <file> /               # 根节点属性（含页边距、默认字体）
officecli get <file> / --json        # JSON 格式输出
officecli get <file> "/body/p[1]"    # 按路径读取特定元素

# CSS 选择器查询
officecli query <file> "paragraph"             # 所有段落
officecli query <file> "run[bold=true]"        # 所有粗体 run
officecli query <file> "shape[text~=Hello]"    # 文本包含 Hello 的形状
```

---

## 创建文档

### 推荐：create + batch

```bash
officecli create output.docx

officecli batch output.docx --commands '[
  {
    "command": "set",
    "path": "/",
    "props": {
      "marginTop": "3.7cm",
      "marginBottom": "3.5cm",
      "marginLeft": "2.8cm",
      "marginRight": "2.6cm",
      "docDefaults.font.eastAsia": "仿宋",
      "docDefaults.fontSize": 16
    }
  },
  {
    "command": "add",
    "parent": "/body",
    "type": "paragraph",
    "props": {
      "text": "文档标题",
      "font": "方正小标宋简体",
      "size": 22,
      "bold": true,
      "align": "center"
    }
  },
  {
    "command": "add",
    "parent": "/body",
    "type": "paragraph",
    "props": {
      "text": "正文内容…",
      "font": "仿宋",
      "size": 16,
      "lineSpacing": "28pt",
      "lineRule": "exact",
      "firstLineIndent": "32pt"
    }
  }
]'
```

### 备选：驻留模式逐条操作

适合需要交互式调整的场景：

```bash
officecli open <file>       # 启动驻留进程，后续操作极快
officecli add <file> /body --type paragraph --prop text="…" --prop font="仿宋" --prop size=16 …
officecli set <file> "/body/p[1]" --prop align="center"
officecli remove <file> "/body/p[3]"
officecli save <file>       # 刷写磁盘（外部程序读取前必须执行）
officecli close <file>      # 刷写并关闭驻留进程
```

> **驻留模式刷写**：空闲 2-10 秒后自动刷写（adaptive）。officecli 自身读取始终可见最新更改，但**外部程序（Word/WPS/预览）读取前必须 `save` 或 `close`**。设 `OFFICECLI_RESIDENT_FLUSH=each` 可在每次操作后立即刷写。

### 模板合并

```bash
officecli merge template.docx output.docx --data '{"name":"张三","date":"2026-07-24"}'
```

将文档中的 `{{key}}` 占位符替换为 JSON 数据。仅做文本替换，不涉及条件逻辑或循环。

---

## 编辑文档

### 增删改

```bash
# 添加 — parent 指定容器，type 指定元素类型
officecli add <file> /body --type paragraph --prop text="新段落" --prop font="仿宋" --prop size=16
officecli add <file> "/body/p[1]" --type run --prop text="加粗文字" --prop bold=true

# 修改
officecli set <file> "/body/p[1]" --prop align="center"
officecli set <file> "/body/p[1]/run[1]" --prop text="修改后的文字" --prop bold=true

# 删除
officecli remove <file> "/body/p[3]"
```

### 移动与交换

```bash
officecli move <file> "/body/p[3]" --to "/body/p[1]"        # 移到第一段之后
officecli move <file> "/body/p[3]" --after "/body/p[1]"     # 指定位置
officecli swap <file> "/body/p[1]" "/body/p[3]"             # 交换两段
```

### 数据导入

```bash
officecli import sheet.xlsx "/sheet[1]" data.csv    # CSV/TSV → Excel
```

---

## GB/T 9704 公文排版

### 排版规范速查

| 元素 | 字体 | 字号 | 关键 props |
|------|------|------|-----------|
| 标题 | 方正小标宋简体 | 22pt | `font="方正小标宋简体" size=22 bold=true align="center"` |
| 一级标题 | 黑体 | 16pt | `font="黑体" size=16 bold=true` |
| 二级标题 | 楷体 | 16pt | `font="楷体" size=16` |
| 正文 | 仿宋 | 16pt | `font="仿宋" size=16 lineSpacing="28pt" lineRule="exact" firstLineIndent="32pt"` |
| 落款/日期 | 仿宋 | 16pt | `font="仿宋" size=16 align="right"` |

页边距：上 3.7cm / 下 3.5cm / 左 2.8cm / 右 2.6cm

### 推荐流程（batch 一步到位）

```bash
officecli create 公文.docx

officecli batch 公文.docx --commands '[
  {"command":"set","path":"/","props":{
    "marginTop":"3.7cm","marginBottom":"3.5cm",
    "marginLeft":"2.8cm","marginRight":"2.6cm",
    "docDefaults.font.eastAsia":"仿宋","docDefaults.fontSize":16
  }},
  {"command":"add","parent":"/body","type":"paragraph","props":{
    "text":"关于XX的请示","font":"方正小标宋简体","size":22,"bold":true,"align":"center"
  }},
  {"command":"add","parent":"/body","type":"paragraph","props":{
    "text":"主送机关名称（顶格）","font":"仿宋","size":16
  }},
  {"command":"add","parent":"/body","type":"paragraph","props":{
    "text":"正文首段…","font":"仿宋","size":16,
    "lineSpacing":"28pt","lineRule":"exact","firstLineIndent":"32pt"
  }}
]'

officecli validate 公文.docx
```

### 字体对照与注意事项

- **CJK 字体用 `font.ea`**：`font` 同时设置 Latin + EastAsia 两个槽，一般够用；若英文和中文需不同字体，则分别指定 `font.latin` 和 `font.ea`
- **`firstLineIndent` 必须用绝对数值**（如 `"32pt"`），不能用 `"2char"` —— 这是高频报错点
- **每个 add paragraph 必须显式指定 `font`**，否则回落 docDefaults（Times New Roman），中文显示异常
- **`size` 不是 `fontSize`** —— prop 名为 `size`

---

## 表格

### 简单表格

```bash
officecli add <file> /body --type table \
  --prop cols=3 \
  --prop data="列1,列2,列3;行1数据A,行1数据B,行1数据C;行2数据A,行2数据B,行2数据C" \
  --prop border.all="single;4;000000"
```

`data` 格式：逗号分隔列，分号分隔行。第一行为表头。

### 逐格操作（需要单独设置单元格样式时）

```bash
# 创建表格框架
officecli add <file> /body --type table --prop cols=4 --prop border.all="single;4;000000"

# 逐格填充
officecli add <file> "/body/table[1]/row[1]" --type cell --prop text="表头1"
officecli add <file> "/body/table[1]/row[1]" --type cell --prop text="表头2"
# ...

# 追加新行
officecli add <file> "/body/table[1]" --type row
officecli add <file> "/body/table[1]/row[last]" --type cell --prop text="数据"
```

---

## Excel 速查

```bash
# 写入单元格
officecli add sheet.xlsx "/sheet[1]" --type row
officecli add sheet.xlsx "/sheet[1]/row[1]" --type cell --prop value=42
officecli add sheet.xlsx "/sheet[1]/row[1]" --type cell --prop value="文本"

# 末尾追加行
officecli add sheet.xlsx "/sheet[1]" --type row
officecli add sheet.xlsx "/sheet[1]/row[last]" --type cell --prop value="新数据"

# 修改单元格
officecli set sheet.xlsx "/sheet[1]/row[1]/cell[1]" --prop value=100
```

---

## PowerPoint 速查

```bash
# 添加幻灯片
officecli add deck.pptx /presentation --type slide

# 添加形状
officecli add deck.pptx "/slide[last]" --type shape \
  --prop text="标题" --prop x=1cm --prop y=1cm --prop w=20cm --prop h=3cm

# 修改形状
officecli set deck.pptx "/slide[1]/shape[1]" --prop text="新标题"
```

---

## 校验与调试

```bash
officecli validate <file>               # 对照 OpenXML schema 校验
officecli view <file> issues            # 格式问题检查
officecli watch <file>                  # 浏览器实时预览（修改后自动刷新）
officecli unwatch <file>                # 停止预览

# 万能底牌：原始 XML 操作
officecli raw <file> /word/document.xml                          # 查看 XML
officecli raw-set <file> /word/document.xml '<w:p>…</w:p>'       # 直接修改 XML
officecli add-part <file> /word/document.xml                     # 新建部件

# 序列化：将文档导出为可回放的 batch 脚本
officecli dump <file> /
officecli dump <file> "/body/p[1]"
```

---

## 执行前自查

生成 docx 前逐条确认：

1. `create` 已单独执行（不在 batch 内）？
2. 页边距 + `docDefaults` 已在 batch 第一条 set？
3. 所有路径含 `[brackets]` 的已用引号包裹？
4. 每个 add paragraph 的 `font` 已显式指定？
5. 正文设齐 `lineSpacing` + `lineRule` + `firstLineIndent`？
6. `firstLineIndent` 用的是绝对数值（`"32pt"`）而非 `"2char"`？
7. prop 用的是 `size` 而非 `fontSize`？
8. `validate` 通过？
9. 优先使用 `batch` 而非逐条 CLI？

---

## 常见故障排除

| 报错/现象 | 原因 | 解决 |
|-----------|------|------|
| `no matches found: /body/p[1]` | shell 展开方括号为 glob | 路径加引号：`"/body/p[1]"` |
| 中文字体不生效 | 只设了 `font.latin` 没设 `font.ea` | 用 `font`（同时设两个槽）或显式加 `font.ea` |
| `firstLineIndent=2char` 不生效 | 不支持相对单位 | 改为绝对数值 `"32pt"` |
| batch 报 `File not found` | `create` 放在了 batch 数组内 | `create` 必须单独执行，再 `batch` |
| 外部程序（Word）看不到最新修改 | 驻留模式下未刷写 | 执行 `save` 或 `close` |
| 字体显示为 Times New Roman | add paragraph 时没设 `font` | 每个 add paragraph 必须显式 `--prop font="…"` |
| 表格数据不显示 | `data` 格式不对 | 检查：逗号分列、分号分行，无多余空格 |
