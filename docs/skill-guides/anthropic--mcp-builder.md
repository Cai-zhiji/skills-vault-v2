# mcp-builder

> 构建高质量 MCP 服务器（Python FastMCP / Node TS SDK），让 LLM 通过精心设计的工具对接外部服务。

## 1. 一句话理解

`mcp-builder` 是**MCP 服务器的开发指南**：四阶段（深入研究 → 实现 → 评审测试 → 建评测）产出一个"让 LLM 能真正完成任务"的高质量 MCP 服务器。

## 2. 它解决什么问题

MCP 服务器的质量，取决于它能否让 LLM 完成真实任务。一个 API 全但工具难用、命名混乱、错误信息无用的服务器，会让 agent 卡住。本 skill 从设计原则（API 覆盖 vs 工作流工具、命名、上下文管理、错误消息）到实现到评测，全流程把关。

## 3. 核心心智模型

**四阶段**：

1. **深入研究与规划**：理解现代 MCP 设计——**API 覆盖 vs 工作流工具**（不确定时优先全面 API 覆盖，给 agent 组合自由）；命名要清晰、一致前缀（`github_create_issue`）、动作导向；上下文管理要简洁描述 + 可过滤/分页；错误消息要**引导 agent 走向解决方案**。再读 MCP 规范（`modelcontextprotocol.io` sitemap → `.md` 页）。
2. **实现**：Python FastMCP 或 Node/TS MCP SDK。
3. **评审与测试**。
4. **建评测**。

## 4. 一次典型运转

1. 研究：理解设计原则 + 读 MCP 规范。
2. 确定工具集（API 覆盖 + 必要的 workflow 工具）。
3. 用 FastMCP 或 TS SDK 实现。
4. 评审 + 测试。
5. 建评测验证 LLM 能完成任务。

## 5. 何时用 / 何时不用

**用**：构建 MCP 服务器整合外部 API/服务，Python（FastMCP）或 Node/TS（MCP SDK）。

**不用**：不用 MCP 的普通 API 集成。

## 6. 依赖与网络位置

- 是 `anthropic` 来源的技能。
- 附属：文档库（`reference/`）。

## 7. 易错点与坑

- **只做 workflow 不做 API 覆盖**：不确定时优先全面 API 覆盖。
- **命名混乱**：一致前缀 + 动作导向。
- **错误消息只说"失败"**：要带具体建议和下一步。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/mcp-builder/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
