# claude-api

> Claude API / Anthropic SDK 官方参考：模型 id、定价、参数、流式、工具调用、MCP、agents、缓存、token 计费、模型迁移。

## 1. 一句话理解

`claude-api` 是**构建 Claude 应用的权威参考**：选对 surface、识别项目语言、读对应语言的官方文档。它的独特之处是**极强的触发规则**——一看到 Claude/Anthropic/LLM 相关信号就要先读它，绝不凭记忆回答。

## 2. 它解决什么问题

Claude API 的很多形状在 2025–2026 变了（扩展思考、web search 工具类型、PHP 参数名等），你的训练先验可能已过时。本 skill 用 `{lang}/` 文件 + `shared/live-sources.md` 提供"永不过时"的权威来源，并列出**最常见的 API 漂移点**对照表，防止写出旧 API 的代码。

## 3. 核心心智模型

**永远从文档取 SDK 用法，绝不猜。** 函数名、类名、命名空间、方法签名、import 路径必须来自显式文档——`{lang}/` 文件或官方 SDK 仓库。**绝不**混用官方 SDK 和 raw HTTP（除非用户明确要 cURL/无官方 SDK）；**绝不**回退到 OpenAI 兼容 shim。

**几个默认值**：模型默认 `claude-opus-5`；复杂任务默认 adaptive thinking（`thinking: {type: "adaptive"}`）；长输入/长输出/高 `max_tokens` 默认流式。

**触发与跳过**：prompt 提到 Claude/Anthropic/LLM 相关，或任务形如 LLM（agent/MCP/RAG/生成/分类…）就**先读它**；只有明确在做**别的 provider**（OpenAI/GPT/Gemini/Llama/Mistral/Cohere/Ollama）时才跳过。

## 4. 一次典型运转

1. 触发检查：有没有别的 provider 信号？有则停。
2. 扫目标文件有无非 Anthropic 标记（`import openai` 等），有则停并问用户是否切到 Claude。
3. 选 surface（SDK / raw HTTP / agent 等）。
4. 识别项目语言，读 `{lang}/` 文件。
5. 从文档取 SDK 用法写代码，不猜；WebFetch 失败就 compile-fix loop 迭代。

## 5. 何时用 / 何时不用

**用**：任何提到 Claude/Anthropic 的 prompt；任何 LLM 相关问题（定价/模型选择/限制/缓存）；LLM 形态任务（agent/MCP/tool/RAG/LLM-judge/computer-use；生成/摘要/提取/分类/改写/对话）。

**不用（跳过）**：明确在做 OpenAI/GPT/Gemini/Llama/Mistral/Cohere/Ollama 时（用 grep 确认）。

## 6. 依赖与网络位置

- 附属：`{lang}/` 各语言 SDK 参考、`shared/live-sources.md`（官方源）。
- 是 `anthropic` 来源的"参考型"技能。

## 7. 易错点与坑

- **凭训练先验写旧 API**：`budget_tokens` 在 Fable 5/Sonnet 5/Opus 5 上被 400 拒绝，要用 `type: "adaptive"`。
- **混用 SDK 和 raw HTTP**：一个项目里二选一。
- **猜 SDK 用法**：必须来自显式文档。
- **PHP 参数名 bulk 转换**：要逐字段抄文档示例，别整体驼峰化。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/claude-api/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
