# skill-creator

> 创建、改进、评估 Skill：写草稿、跑测试 prompt、定性+定量评测、迭代重写、优化触发描述。

## 1. 一句话理解

`skill-creator` 是**做 skill 的 skill**：从"想做什么"到"写草稿"到"跑测试 prompt 评测"到"按反馈重写"到"优化触发描述"，是一个可循环的迭代流程。

## 2. 它解决什么问题

写一个 skill 容易，写一个**触发准确、行为可靠**的 skill 难。本 skill 用"评测驱动"的循环：写草稿 → 建测试 prompt → 用带 skill 的 Claude 跑 → 定性（人看结果）+ 定量（benchmark 指标）评估 → 重写 → 扩大测试集再试。

## 3. 核心心智模型

**评测驱动的迭代循环。** 高层流程：

1. 决定 skill 做什么、大概怎么做。
2. 写草稿。
3. 建几个测试 prompt，跑带 skill 的 Claude。
4. 帮用户定性 + 定量评估结果（后台跑时起草定量 evals，用 `eval-viewer/generate_review.py` 展示）。
5. 按反馈重写。
6. 循环到满意。
7. 扩大测试集更大规模再试。

之后可用**独立的 description improver 脚本**优化 skill 的触发准确度。

**沟通上注意用户的技术背景**：看到明显的技术语境线索才用 JSON/assertion 这类词，必要时简短解释术语。

## 4. 一次典型运转

用户说"我想做个 X 的 skill"→ 缩小意图 → 写草稿 → 写测试用例 → 定评估方式 → 跑 prompt → 定性+定量评估 → 重写 → 迭代 → 优化触发描述。

## 5. 何时用 / 何时不用

**用**：从零建 skill、改/优化现有 skill、跑 evals 测试、benchmark 性能（方差分析）、优化触发描述。

**不用**：只是**用** skill（不是造/改 skill）。

## 6. 依赖与网络位置

- 附属：`eval-viewer/generate_review.py`、description improver 脚本。
- 是 `anthropic` 来源的元技能。

## 7. 易错点与坑

- **只写不评测**：评测循环是核心，别只写草稿就收工。
- **术语甩给不懂的用户**：看语境线索，必要时解释。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/skill-creator/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
