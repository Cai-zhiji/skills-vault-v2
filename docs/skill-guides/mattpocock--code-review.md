# code-review

> 从某个固定点（commit / branch / tag / merge-base）起，沿两条轴并行评审改动：标准（是否遵循仓库规范）与规格（是否忠实实现原始 issue/spec）。

## 1. 一句话理解

`code-review` 是**双轴并行评审**：把同一份 diff 同时丢给两个子 agent——一个查"写得对不对（符合规范吗）"，一个查"写的是不是要写的（符合规格吗）"——然后把两份报告并排呈现，不做合并、不重新排序。

## 2. 它解决什么问题

单轴评审有个致命盲区：代码可以完全符合规范却实现了错误的东西，也可以完全符合需求却破坏项目约定。把两轴混在一起评分，其中一轴就会掩盖另一轴。`code-review` 用"两个独立子 agent + 分别报告"的结构，从机制上防止这种互相遮蔽。

## 3. 核心心智模型

**标准轴（Standards）与规格轴（Spec）是两条正交的评判线，永远分开报告。**

- 标准轴除了读仓库自带的 `CODING_STANDARDS.md`/`CONTRIBUTING.md`，还**始终附带一份 Fowler 代码坏味道基线**（神秘命名、重复代码、霰弹式修改、投机泛化等 12 条）。两条规则：仓库标准覆盖基线；每条坏味道都是"标注的启发式"，不是硬性违规，工具已强制检查的跳过。
- 规格轴只回答三件事：规格要求了什么却缺失/不完整；diff 里出现了没被要求的东西（范围蔓延）；看起来实现了但实现得不对的地方。

## 4. 一次典型运转

用户说"review since main"：

1. **钉住固定点**：`git diff main...HEAD`（三点，对 merge-base 比较），`git rev-parse` 确认 ref 有效、diff 非空——坏 ref 或空 diff 在这里就失败，而不是在两个子 agent 里失败。
2. **找规格源**：按 commit message 里的 issue 引用 → 用户传的路径 → `docs/`/`specs/` 下匹配的文件 → 都没有就问用户。没有规格则规格轴子 agent 跳过并注明。
3. **找标准源** + 附上坏味道基线全文。
4. **并行派两个子 agent**，各自拿到 diff 命令、commit 列表、相关源文件，要求 400 字内、区分硬违规与判断性调用。
5. **聚合**：分别放在 `## Standards` 和 `## Spec` 下，**不合并、不重排**；结尾各轴一句小结（各轴发现数 + 各轴内最严重问题），不跨轴选"总冠军"。

## 5. 何时用 / 何时不用

**用**：评审一个分支、PR、进行中的改动，或"review since X"。

**不用**：没有明确固定点/规格的散点代码改进——那更像 `improve-codebase-architecture` 的活。

## 6. 依赖与网络位置

- 依赖 `setup-matt-pocock-skills` 配好的 issue tracker（找不到 `docs/agents/issue-tracker.md` 就先跑它）。
- 是 `implement` 的收尾环节（实现完用 `code-review` 自查）。
- 用 `codebase-design` 的术语（module/interface/seam）做语言底座。

## 7. 易错点与坑

- **合并/重排两条轴**：这是它刻意要防止的——"哪轴最严重"是跨轴重排，别做。
- **跳过坏味道基线**：即使仓库没写任何规范，标准轴也要跑那 12 条 Fowler 坏味道。
- **硬违规 vs 判断**：只有"违反文档化标准"才可能是硬违规；基线坏味道永远是判断性调用。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/engineering/code-review/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
