# improve-codebase-architecture

> 扫描代码库找出"深化"机会，以可视化 HTML 报告呈现，然后对你选中的那一个进行拷问。

## 1. 一句话理解

`improve-codebase-architecture` 是 `codebase-design` 的**行动版**：先探索代码库的"摩擦点"，找出哪些浅模块值得深化，产出一份带 before/after 图的 HTML 报告让用户挑，再对被选中的候选跑一轮拷问。

## 2. 它解决什么问题

代码库的架构债是累积的——耦合模块泄漏接缝、纯函数被抽出来只为可测但真正的 bug 藏在调用方式里、模块浅到接口和实现一样复杂。这些不会自己暴露。本 skill 主动扫描并把它们变成可挑选的"深化候选"，还给出每个的收益（局部性 + 杠杆 + 测试改善）。

## 3. 核心心智模型

**YAGNI 先定范围，再扫描。** 深化一个模块的回报是"未来改它更容易"，所以把权重放在**最近频繁改动**的代码——先看 commit history 找热区，而不是漫无目的地扫全库。

**用 `CONTEXT.md` 的领域词汇 + `codebase-design` 的架构词汇说话。** 比如 `CONTEXT.md` 定义了 "Order"，就说"Order intake 模块"，不说"FooBarHandler"也不说"Order service"。

**删除测试是信号。** 怀疑某模块浅，就问：删掉它，复杂度是"集中"（好的信号）还是"只是挪了个地方"？

## 4. 一次典型运转

1. **探索**：用户指定方向就直接去，否则 `git log` 找热区 → 读 `CONTEXT.md` 和 ADR → 派子 agent 有机探索摩擦点。
2. **出 HTML 报告**（写到 `$TMPDIR`，不进仓库，`open` 打开）：每个候选一张卡，含 Files / Problem / Solution / Benefits / before-after 图 / 推荐强度（Strong / Worth exploring / Speculative）；结尾给 Top recommendation。**不要在这一步就提接口。**
3. **拷问循环**：用户挑一个 → 跑 `/grilling` 走决策树（约束、依赖、深化后模块形状、接缝背后放什么、哪些测试存活），边问边用 `/domain-modeling` 更新术语/写 ADR。

## 5. 何时用 / 何时不用

**用**：想找代码库结构改进机会、减少架构摩擦、提升可测性与 AI 可导航性时。

**不用**：已经明确要评审某次改动（`code-review`）；只是设计单个模块接口（`codebase-design`）。

## 6. 依赖与网络位置

- 依赖 `codebase-design`（词汇）与 `domain-modeling`（术语/ADR）。
- 交互式拷问用 `grilling`。
- 附属：`HTML-REPORT.md`（报告脚手架与图模式）。
- 是 `diagnosing-bugs` 收尾时"架构问题"的交接去向。

## 7. 易错点与坑

- **不先定范围就扫全库**：YAGNI——先找热区，别平均用力。
- **报告写进仓库**：必须写到临时目录，别污染 repo。
- **一上来就提接口**：报告阶段只出候选，接口设计留给拷问阶段。
- **忽视 ADR 冲突**：候选若和既有 ADR 矛盾，只在摩擦真实到值得重开 ADR 时才标注。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/engineering/improve-codebase-architecture/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
