# doc-coauthoring

> 引导用户走过协作写文档的结构化流程：上下文收集 → 精炼与结构 → 读者测试。

## 1. 一句话理解

`doc-coauthoring` 是一个**三阶段协作写文档向导**：先把用户脑中的上下文搬出来（Context Gathering），再逐节头脑风暴与编辑（Refinement & Structure），最后用一个无上下文的全新 Claude 测试文档有没有盲点（Reader Testing）。

## 2. 它解决什么问题

写文档最大的坑是**作者的盲点**——你脑子里有的上下文，读者（或另一个 Claude）没有。本 skill 用"读者测试"专门解决这个：用全新 Claude（无上下文）读文档，看它在没你脑子里那些背景时会误解什么。

## 3. 核心心智模型

**三阶段**：

1. **Context Gathering**：先问 meta 问题（文档类型？读者？期望影响？有无模板？），用户可用速记或 dump 的方式回答——目标是拉近"用户知道的"和"Claude 知道的"。
2. **Refinement & Structure**：每节通过澄清问题 → 头脑风暴 → 策展 → 缺口检查迭代构建。
3. **Reader Testing**：让一个全新 Claude（无上下文）读，抓盲点，再给别人读。

**触发**：用户提"write a doc / draft a proposal / create a spec / PRD / design doc / decision doc / RFC"等，先**提议**这个工作流，用户拒绝就自由发挥。

## 4. 一次典型运转

1. 识别到写文档意图，提议三阶段流程，问要不要走。
2. 接受 → Stage 1 问 meta 上下文，用户 dump 信息。
3. Stage 2 逐节头脑风暴/编辑/策展/查缺口。
4. Stage 3 用全新 Claude 测试盲点，修订。

## 5. 何时用 / 何时不用

**用**：写文档、提案、技术规格、决策文档、PRD/design doc/RFC，或用户要开始一个实质写作任务。

**不用**：用户明确要自由发挥、不想要结构化流程时。

## 6. 依赖与网络位置

- 是 `anthropic` 来源的文档协作技能。
- 与 `docx`（生成 Word）互补——本 skill 管"内容怎么写"，docx 管"怎么落成 .docx"。

## 7. 易错点与坑

- **跳过 Reader Testing**：盲点测试是它相对普通写作的最大增量。
- **强推流程**：用户拒绝就自由发挥，别硬套。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/doc-coauthoring/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
