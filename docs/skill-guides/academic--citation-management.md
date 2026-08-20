# citation-management

> 系统化的学术引用管理：搜索 Google Scholar/PubMed、从多源提取准确元数据、校验引用、生成规范 BibTeX。

## 1. 一句话理解

`citation-management` 负责**引用这件事的全流程**：找论文、提取元数据（作者/标题/期刊/年份）、把 DOI/PMID/arXiv ID 转成 BibTeX、校验已有引用、清理去重、建参考文献。

## 2. 它解决什么问题

引用错误（拼错作者、错年份、错期刊）是论文的硬伤，也极难事后排查。手动从 Google Scholar 复制引用常带格式脏数据。本 skill 把"搜索 → 提取 → 校验 → 格式化"系统化，保证引用准确、可复现。

## 3. 核心心智模型

**多源交叉提取 + 校验。** 从 CrossRef、PubMed、arXiv 等多个来源提取元数据，互相校验；把 DOI/PMID/arXiv ID 转成规范 BibTeX；对已有引用做准确性核对和去重。它和 `literature-review` 无缝集成（后者做系统综述，本 skill 管其中引用这一环）。

## 4. 一次典型运转

1. 确定要找的论文（主题搜索 / DOI / PMID / arXiv ID）。
2. 用 Google Scholar / PubMed 搜索。
3. 从 CrossRef/PubMed/arXiv 提取完整元数据。
4. 校验信息与真实发表一致。
5. 生成规范 BibTeX，去重、统一格式。

## 5. 何时用 / 何时不用

**用**：找论文、DOI/PMID/arXiv 转 BibTeX、提取引用元数据、校验引用、清理 BibTeX、查高被引论文、建参考文献。

**不用**：需要做完整系统综述（用 `literature-review`，本 skill 是它的一环）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 与 `paper-lookup`（查库）、`literature-review`（综述）协同。

## 7. 易错点与坑

- **编造元数据**：作者/期刊/年份/DOI 一律不得捏造，从来源提取。
- **重复引用未去重**：检查重复条目。
- **格式不统一**：同一篇文献多库格式不一，要统一到一种。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/citation-management/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
