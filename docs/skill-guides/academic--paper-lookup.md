# paper-lookup

> 通过 REST API 检索 10 个学术论文库：PubMed、PMC、bioRxiv、medRxiv、arXiv、OpenAlex、Crossref、Semantic Scholar、CORE、Unpaywall。

## 1. 一句话理解

`paper-lookup` 是**论文检索的 API 路由**：判断你的查询该打哪个库（或多个库），读对应 reference，调 API，返回原始结果。

## 2. 它解决什么问题

"找某篇论文 / 找某主题的论文 / 找某作者的出版物 / 找开放获取 PDF / 找全文"，各自对应不同的库。本 skill 提供一个"按用途选库"的决策表，并强制返回**原始 JSON/XML**（而不是只给摘要），避免信息丢失。

## 3. 核心心智模型

**按用途选库**：

| 用户问 | 主库 | 备选 |
| --- | --- | --- |
| 生物医学主题论文 | PubMed | Semantic Scholar、OpenAlex |
| 生物医学全文 | PMC | CORE |
| 预印本 | arXiv / bioRxiv / medRxiv | |
| DOI/元数据 | Crossref | |
| 开放获取 PDF | Unpaywall | |

**返回三样东西**：每个库的原始 JSON（arXiv 用解析后 XML）、命中的库与具体 endpoint、以及"某个查询无结果"要明说（不能省略）。

## 4. 一次典型运转

1. 理解查询意图（DOI？主题？作者？全文？）。
2. 按决策表选库。
3. 读 `references/` 里对应库的 reference（endpoint、查询格式、示例）。
4. 调 API。
5. 返回原始结果 + 命中库清单。

## 5. 何时用 / 何时不用

**用**：查论文、引用、DOI/PMID、摘要、全文、开放获取、预印本、引用图、作者检索、任何学术文献查询。

**不用**：做完整系统综述（`literature-review` 用 parallel-web 广搜）；管理引用格式（`citation-management`）。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 附属 `references/` 每个库一个 reference。
- 部分库需/受益于 API key（key 从环境变量加载）。

## 7. 易错点与坑

- **无结果不说明**：某库返回空要明确说，不能省略。
- **只回摘要不回原始**：要返回原始 JSON/XML。
- **API key 泄露**：key 从环境变量加载，不写进代码/输出。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/paper-lookup/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
