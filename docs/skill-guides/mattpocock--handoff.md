# handoff

> 把当前对话压缩成一份交接文档，让另一个 agent 能接手继续。

## 1. 一句话理解

`handoff` 产出一份**交接文档**，概括当前会话进展，让一个全新 agent 能接续工作。文档存到用户操作系统的临时目录（**不是**当前工作区），并附一个"suggested skills"建议清单。

## 2. 它解决什么问题

当上下文要跨会话/跨 agent 传递时，原始对话太长、太散。`handoff` 把它压缩成一份可携带的文档——只写"下一步需要什么"，指向已有的 spec/plan/ADR/issue/commit/diff 而不是复制它们。

## 3. 核心心智模型

**引用，不复制。** 已经落在其他产物（spec、plan、ADR、issue、commit、diff）里的内容，不要重复写进交接文档，用路径或 URL 引用即可。

**脱敏。** API key、密码、PII 都要 redact。

**参数 = 下一会话焦点。** 用户传的参数当作"下一会话要聚焦什么"来定制文档。

## 4. 一次典型运转

1. 概括当前状态与下一步。
2. 加"suggested skills"建议清单。
3. 引用已有产物而非复制。
4. 脱敏。
5. 存到 OS 临时目录（非工作区）。

## 5. 何时用 / 何时不用

**用**：需要把工作交给另一个 agent、另一个会话继续时。

**不用**：同一会话内继续（用 `compact` 或继续当前上下文）。

## 6. 依赖与网络位置

- 与 `claude-handoff` 孪生（后者不存文件、直接起后台 agent）。
- 是 `ask-matt` 阶段边界决策里的一个选项（跨工具/目录/人员传递时用）。

## 7. 易错点与坑

- **复制已有产物**：要引用路径/URL，别重复内容。
- **存错地方**：存 OS 临时目录，不是工作区。
- **忘脱敏**：文档可能成为下一个 agent 的 prompt。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/productivity/handoff/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
