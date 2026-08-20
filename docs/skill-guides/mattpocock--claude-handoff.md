# claude-handoff

> 把当前对话交给一个新的后台 agent，立即接手工作。

## 1. 一句话理解

`claude-handoff` 与 `handoff` 同源，但**不存文件**：它把交接摘要作为 prompt，直接启动一个后台 agent——`claude --bg --name "<名称>" "<摘要>"`——在当前工作目录起步，立即返回。

## 2. 它解决什么问题

当工作可以独立地交给后台继续、你不想被阻塞时，`claude-handoff` 让"交接"变成"启动一个新 agent"这一个动作，而不是写文件再等人读。

## 3. 核心心智模型

**摘要即 prompt。** 交接摘要会直接成为新 agent 的初始 prompt，所以：

- 必须**脱敏**（API key、密码、PII）——它会变成 prompt。
- 必须带 `-n`/`--name` 描述性名称（如 `--name "Fix login bug"`），它决定任务列表、会话选择器、终端标题里显示的名字。
- 附 "suggested skills" 建议清单。
- **引用不复制**：已在 spec/plan/ADR/issue/commit/diff 里的内容，用路径或 URL 引用。
- 参数 = 下一会话焦点。

## 4. 一次典型运转

1. 写交接摘要（含 suggested skills）。
2. 脱敏。
3. `claude --bg --name "<名称>" "<摘要>"`，立即返回，用户用 `claude agents` 管理。

## 5. 何时用 / 何时不用

**用**：要立即把工作交接给后台 agent 继续时。

**不用**：要留一份文档给人/给未来会话读（用 `handoff`）；工作不能并行独立完成。

## 6. 依赖与网络位置

- 依赖 `claude` CLI 的 `--bg` 能力（Claude Code 后台 agent）。
- 是 `handoff` 的"直接起 agent"孪生。

## 7. 易错点与坑

- **忘 `--name`**：一定要带描述性名称，否则任务列表里无法识别。
- **忘脱敏**：摘要就是 prompt，敏感信息会暴露给新 agent。
- **复制已有产物**：引用路径/URL，别重复内容。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/in-progress/claude-handoff/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
