# git-guardrails-claude-code

> 给 Claude Code 装 hooks，在执行前拦截危险的 git 命令（push、reset --hard、clean、branch -D 等）。

## 1. 一句话理解

`git-guardrails-claude-code` 装一个 PreToolUse hook，在 Claude 执行危险 git 命令**之前**拦截并阻止，让 Claude 看到"无权访问这些命令"的消息。

## 2. 它解决什么问题

`git push`（尤其 `--force`）、`reset --hard`、`clean -fd`、`branch -D`、`checkout .`/`restore .` 这类命令会破坏性改仓库状态，且 agent 一旦执行就不可逆。这个 skill 用一个 hook 在 Bash 工具调用前把它们拦下来，加一层保险。

## 3. 核心心智模型

**PreToolUse hook + Bash matcher。** 核心是 `scripts/block-dangerous-git.sh`：一个 shell 脚本，接到 Claude 即将执行的 Bash 命令，匹配到黑名单就返回退出码 2 + BLOCKED 消息。把它挂进 `.claude/settings.json` 的 `hooks.PreToolUse`，`matcher` 设为 `Bash`。

**作用域二选一**：本项目（`.claude/settings.json`）或全局所有项目（`~/.claude/settings.json`）。

## 4. 一次典型运转

1. 问作用域（本项目 / 全局）。
2. 拷 `scripts/block-dangerous-git.sh` 到目标位置（`.claude/hooks/` 或 `~/.claude/hooks/`），`chmod +x`。
3. 把 hook 加进对应 `settings.json`（已存在则 merge 进 `hooks.PreToolUse`，别覆盖其他设置）。
4. 问是否要增删黑名单模式，编辑脚本。
5. 验证：`echo '{"tool_input":{"command":"git push origin main"}}' | <脚本>` 应退出码 2 并打印 BLOCKED。

## 5. 何时用 / 何时不用

**用**：想防止破坏性 git 操作、加 git 安全 hook、阻止 Claude Code 里的 push/reset 时。

**不用**：不需要这种保护，或你确实要 agent 自由 push/reset 的场景。

## 6. 依赖与网络位置

- 依赖 Claude Code 的 hooks 机制（`settings.json`）。
- 附属：`scripts/block-dangerous-git.sh`。

## 7. 易错点与坑

- **覆盖已有 settings**：要 merge 进现有 `hooks.PreToolUse`，别整体覆盖。
- **忘 chmod +x**：脚本不可执行就拦不住。
- **作用域问清**：项目级和全局级落点不同。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/misc/git-guardrails-claude-code/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
