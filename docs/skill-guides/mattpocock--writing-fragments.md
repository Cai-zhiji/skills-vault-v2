# writing-fragments

> 写作·探索（explore）：挖掘原始碎片（fragment），不建任何结构。

## 1. 一句话理解

`writing-fragments` 是"写作三件套"里**纯探索**的一步：通过拷问把"可能写的东西"拓展开，产出**碎片**追加进一个 Markdown 文件，**不碰结构**（结构是 exploit 的活，另一个 skill）。

## 2. 它解决什么问题

好文章常常死于过早定结构——还没想清就硬套大纲。`writing-fragments` 把"探索"和"开发"切成两个独立 skill，先让碎片自由积累，结构留到 `writing-shape`/`writing-beats` 再定。

## 3. 核心心智模型

**Fragment 的标准是"这是不是一段好文字"，不是"这是不是一个自足的论证"。** 碎片要让**作者**能看懂，但不必定义术语、不必让冷读者读懂。它天然异质：一个尖句子、一个带一句理由的主张、一段小场景、一个半成想法、一句引语、一簇靠感觉聚在一起的观察、一句抱怨、一个 punchline。

**Leading word 是最值钱的碎片。** 一个能挂起整篇文章的紧凑比喻/造词（像 `tracer bullets`、`fog of war` 那样给整个模式命名）。在 explore 阶段起对一个，会在 exploit 阶段塑造结构、过渡、标题——全程分红。当对话绕着一个反复出现的想法打转时，逼着自己为它造一个词。

**文件格式**：顶部一个 H1 工作标题（可变），其余只有碎片，用 `---` 分隔；正文无标题、无 tag、无顺序（按加入顺序）。

**写作节奏**：静默 append，不逐条请求许可，顺带提一句"加了那个"；写前从磁盘重读，绝不覆盖，只 append（或按用户要求就地改某条）；"删最后一条/重写更尖/合并那两条"都是一等指令。

## 4. 一次典型运转

用户想写某话题 → 起拷问会话 → 双方冒出的碎片 append 进一个文件 → 抓第一句（含初始 prompt）开始 → 首写放 H1 工作标题 + 第一个碎片 → 持续静默 append → 直到素材够了交给 exploit。

## 5. 何时用 / 何时不用

**用**：想先挖掘素材、不急着定结构时。

**不用**：素材已够、要成文了（`writing-shape`/`writing-beats`）。

## 6. 依赖与网络位置

- 是 mattpocock"写作三件套"的 explore 起点。
- 下游是 `writing-shape`（逐段成文）或 `writing-beats`（逐拍成文）。

## 7. 易错点与坑

- **过早定结构**：本 skill 明确 out of scope——分阶段、大纲、结构都不碰。
- **漏抓第一句**：要从用户最初那句话开始抓碎片（含初始 prompt）。
- **写前不重读**：用户可能已编辑/重排/删碎片，要保留。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/in-progress/writing-fragments/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
