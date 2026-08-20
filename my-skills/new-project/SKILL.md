---
name: new-project
description: 新项目冷启动：按功能域建文档化骨架 + 本地 git。按需接入 grill-with-docs / wayfinder / to-spec。
disable-model-invocation: true
---

# 新项目冷启动

为一个新项目建立**文档化骨架** + **本地 git**。第一层按功能域组织，三层文档（指针/词汇/状态）就位，首次 commit 完成。

## 步骤

1. **确认目录** — 工作目录应基本为空。若非空，询问用哪个子目录。
   ✅ 完成：目录确定，可安全写入。

2. **选定范围方式（检查点·需用户选择）**
   - `/grill-with-docs` — 大约一个会话能理清的想法 → `CONTEXT.md` + `docs/adr/`
   - `/wayfinder` — 一个会话装不下、需要决策地图 → issue tracker 决策票（默认 local-markdown）
   - 快速起步 → 轻量版 grill-with-docs（只写 `CONTEXT.md`）
   - ✅ 完成：`CONTEXT.md` 已建（或用户明确跳过）。

3. **生成 spec** — `/to-spec` → `docs/specs/<项目>.md`。若 wayfinder 地图已含 spec 则跳过。
   ✅ 完成：spec 存在（或明确跳过）。

4. **建骨架** — 按 `templates/skeleton.md` 创建目录树。空目录放 `.gitkeep`；**不预填 `app/` `server/`**（交给框架脚手架）。
   ✅ 完成：所有顶层域存在，`app/` `server/` 为空。

5. **写入口文档** — 按 `templates/CLAUDE-AGENTS.md` 写 `CLAUDE.md` + `AGENTS.md`；按 `templates/STATUS.md` 写 `docs/STATUS.md`，用步骤 2 的信息填充目标/进度/下一步。
   ✅ 完成：三个文件就位且内容非空。

6. **git init** — 写 `.gitignore`（`templates/gitignore.md`），首次 commit `chore: 项目初始化，建立文档化骨架`。**永不 push**。
   ✅ 完成：commit 已建，`git log` 可见。

7. **检查点·确认** — 展示骨架树 + STATUS.md 给用户，确认后结束。

## 铁律
- 本地 git only，**永不 push 云端**。
- commit 用简短中文（`feat:` / `fix:` / `chore:`）。
- `app/` `server/` 内容由脚手架决定，**不要预填**。
- 三层文档分工别混淆：`CLAUDE/AGENTS.md` = 精简指针，`CONTEXT.md` = 词汇表，`docs/STATUS.md` = 状态。

## 模板
模板在 skill 目录下：
- `templates/skeleton.md` — 目录骨架树
- `templates/CLAUDE-AGENTS.md` — CLAUDE.md / AGENTS.md
- `templates/STATUS.md` — 状态文档
- `templates/gitignore.md` — .gitignore
