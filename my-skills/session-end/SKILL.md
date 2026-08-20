---
name: session-end
description: 会话结束仪式：更新 STATUS、检查 CONTEXT、写一篇 devlog、commit。保持项目"渐进性增长"。
disable-model-invocation: true
---

# 会话结束仪式

一个 agent 会话结束时收尾：让项目文档反映当下状态，让下一个 agent 冷启动即可接手。

## 会话 = 一次 devlog 的单位
一次连续 agent 会话。**不是** commit 粒度 — commit 是更细的（每变更一次），贯穿会话全程；本仪式是会话级收尾。

## 步骤

1. **更新 `docs/STATUS.md`** — 反映当前现实：
   - `当前进度`：完成项移到 done，标注进行中。
   - `下一步`：重写为下一个 agent 该先做的事。
   - `关键约束/约定`：补充本次学到的（栈、环境、决策）。
   - **现状文档，不是历史** — 历史归 devlog。
   - ✅ 完成：STATUS 准确描述当前 + 明确的下一步。

2. **检查 `CONTEXT.md`** — 本次会话有没有**新领域词汇**或**澄清了模糊概念**？有就增补（glossary only，不写实现细节）。没有就不动。
   - ✅ 完成：有则增补，无则未改动。

3. **追加 devlog** — 每会话一篇 `docs/devlog/YYYY-MM-DD-<slug>.md`，按 `templates/devlog.md`。
   - **只增不改**：永不编辑历史条目。
   - ✅ 完成：新文件存在，五个小节都填了（无内容的小节写"无"）。

4. **commit** — 代码 + 文档一起，一个 commit，消息 `chore: 会话结束，更新文档与日志`（或概括会话主题）。**永不 push**。
   - ✅ 完成：commit 已建，`git log` 可见。

## 铁律
- 本地 git only，**永不 push**。
- devlog **只增不改** — 它是历史；STATUS 才是现状。
- 文档与代码同 commit，让 `git log` 把整个会话作为一个可追溯单元。
- 会话中若完成一个独立功能，照常在会话中途 commit；本仪式的 commit 是收尾的那个。

## 模板
- `templates/devlog.md` — devlog 条目模板
