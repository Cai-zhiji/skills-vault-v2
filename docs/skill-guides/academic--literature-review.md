# literature-review

> 系统的、全面的文献综述：多库检索、主题综合、逐条核验引用、生成专业的 Markdown 与 PDF 文档。

## 1. 一句话理解

`literature-review` 做**系统综述**这件事：用严格学术方法搜多库、按主题综合、核验每条引用、产出 Markdown 和 PDF 格式的专业文档。

## 2. 它解决什么问题

写综述、做 meta 分析、写论文的文献综述章节、调查领域现状、找研究缺口——这些需要"系统、可复现、引用准确"的检索与综合。本 skill 用 `parallel-web`（`parallel-cli search`）做广撒网检索，辅以专用数据库访问（gget、bioservices、datacommons-client），再配引用核验、结果聚合、文档生成。

## 3. 核心心智模型

**五阶段流程**：规划与界定范围 → 系统检索 → 筛选与选择 → 数据提取与合成 → 综合与分析。产出带**已验证引用**、多引用风格（APA/Nature/Vancouver 等）的文档。

**一个硬性要求**：每篇综述必须包含至少 1–2 张 AI 生成的科学示意图（用 `scientific-schematics`），没有视觉元素的综述是不完整的。

## 4. 一次典型运转

定主题与范围 → `parallel-cli search` 多库检索 → 按纳入/排除标准筛选 → 提取数据（方法、结果、局限）→ 主题综合 → 核验引用 → 生成含示意图的 Markdown/PDF。

## 5. 何时用 / 何时不用

**用**：系统综述、跨源综合知识、meta 分析/scoping review、论文综述章节、查领域现状、找研究缺口。

**不用**：单篇文献查找（`paper-lookup`）；单纯引用管理（`citation-management`）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 内部用 `parallel-web`、`citation-management`、`scientific-schematics`。

## 7. 易错点与坑

- **漏掉科学示意图**：这是强制要求，综述必须配 1–2 张 AI 图。
- **引用不核验**：综述的引用必须逐条核验，不能直接采信。
- **按篇流水账综合**：要按主题综合，不是一篇篇罗列。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/literature-review/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
