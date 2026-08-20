# drawio-skill

## 1. 一句话理解

这是一个把结构化需求变成可编辑 `.drawio` 图，并经过结构校验、视觉审阅和多格式导出的图表生产线。

## 2. 它解决什么问题

复杂系统的关系很难只靠文字表达，手工画图又容易出现重叠、断线、裁切、边标签碰撞和交付格式不统一。普通 diagrams-as-code 适合 Markdown 中的结构图，却不一定提供 draw.io 的丰富形状、泳道、品牌图标和可编辑导出。这个 skill 把“理解关系、生成 XML、检查可读性、交付 PNG/SVG/PDF/JPG”串成闭环，并在工具不可用时提供浏览器或 XML 退化路径。

## 3. 核心心智模型

**图不是一次性图片，而是经过两道检查的可编辑模型。** 第一层是结构模型：节点、父容器、`source`/`target`、唯一 id、几何位置和边路由必须自洽；第二层是视觉模型：导出的预览中不能有重叠、裁切、离画布、错连或标签遮挡。只有两层都过关，才把同一份 XML 导出为带嵌入模型的最终文件。

因此工作流有明确的“预览—修正—定稿”分界：预览 PNG 不用 `-e`，避免视觉模型无法读取；最终 PNG/SVG/PDF 才使用 `-e` 保留可编辑性，PNG 还要修复 draw.io CLI 截断的 IEND。用户反馈若只涉及单个节点就原地改 XML，若改变整体方向才重生成布局。

## 4. 一次典型运转

先确认图表类型、输出格式、范围和技术标签；若用户已经说清或需求很简单，就直接开始。解析是否有命名的 style preset，并按用户目录优先、内置目录其次加载；没有明确 preset 时才使用默认约定。然后确认本机实际可用的 `drawio` / `draw.io` CLI 名称。

根据图表类型选择 preset 或 bundled generator：标准流程可用 Mermaid 转换，序列图、C4、ERD、代码/基础设施导入图等可用对应脚本；手写 XML 前先读 `references/xml-authoring.md`，需要特定 AWS、UML、BPMN 或 AI 图标时用 `shapesearch.py` / `aiicons.py`。生成后先跑 `validate.py`，检查 dangling edges、重复/保留 id、父节点和重叠，再用 CLI 生成不带 `-e`、宽度不超过 2000 的预览 PNG。具备 vision 时最多进行两轮自检并自动修正，再把同一文件交给用户评审。

用户提出颜色、节点、位置、尺寸、连接或标签修改时，只改对应 XML；直到用户批准后，按要求输出 PNG、SVG、PDF 或 JPG。最终 PNG 使用 `-e`、双扩展名如 `diagram.drawio.png`，并立即运行 `scripts/repair_png.py`；若 CLI 缺失，则生成 diagrams.net viewer/editor URL，或只交付 `.drawio` XML。

## 5. 何时用 / 何时不用

**适合用：** 需要精确、可编辑、可导出的架构图、网络拓扑、ERD、UML、SysML、BPMN、泳道图、C4、ML/DL 模型图，以及从 Terraform、Kubernetes、代码、OpenAPI 或 SQL 生成关系图的场景。

**不要用：** 追求手绘白板风格时用 `excalidraw` / `tldraw`；只想让图表作为 Markdown 中的 diagrams-as-code 时用 `mermaid` 或 `plantuml`；需要自由手绘和无限画布时也不要强行套 draw.io。

## 6. 依赖与网络位置

- 核心依赖是 macOS、Linux 或 Windows 上可调用的 draw.io desktop CLI；vision 自检需要视觉能力，Graphviz `dot` 只供可选自动布局使用。
- 资源按需分层：`diagram-types.md` 管结构 preset，`xml-authoring.md` 管手写 XML，`style-presets.md` 管样式，`troubleshooting.md` 管故障；`validate.py`、`repair_png.py` 和 `encode_drawio_url.py` 分别承担结构检查、PNG 修复和浏览器回退。
- 与 `mermaid`、`excalidraw`、`plantuml` 是相邻路由，不是互相替代；与本仓库其他 `pdf` skill 的同名能力有交集，但本 skill 的主产物是图，PDF 只是导出格式。
- 平台兼容：Codex、Claude；操作系统支持 macOS、Linux、Windows。

## 7. 易错点与坑

- 预览阶段误用 `-e`，视觉 API 可能因 PNG IEND/嵌入块问题返回 400；预览必须省略 `-e`，最终 PNG 才使用并修复。
- 用 `-s 2` 导出预览导致超过 2576×2576；预览应用 `--width 2000`，不要把 `-w` 当作缩写。
- 误以为 CLI 的 `--layout` 只会重新路由边；ELK layout 会移动节点，未知 preset 还可能弹窗并让 headless 任务挂住。
- 手写 XML 时复用 `0`/`1`，或给 edge 省略 `<mxGeometry relative="1" as="geometry" />`，会导致图不渲染或关系失效。
- 只看结构 lint 不看图片；边可能结构上连对了，却穿过无关节点或与标签重叠，必须做视觉自检和用户评审。
- draw.io CLI 在受限 macOS sandbox 中崩溃或无输出时不要反复重试，改用浏览器 fallback、XML-only，或让用户在非 sandbox 环境导出。
- 没有 CLI 时不应假装已经导出图片；应明确交付 XML/URL，并说明手动导出路径。

## 8. 出处

- 原始路径：`sources/drawio-skill/skills/drawio-skill/SKILL.md`
- 上游 commit：`2ee141e`
- 平台兼容：Codex、Claude；操作系统支持 macOS、Linux、Windows

