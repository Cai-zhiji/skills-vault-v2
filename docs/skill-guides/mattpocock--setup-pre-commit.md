# setup-pre-commit

> 在当前仓库装 Husky pre-commit hooks + lint-staged（Prettier）+ 类型检查 + 测试。

## 1. 一句话理解

`setup-pre-commit` 给当前 repo 配一套提交前钩子：Husky 触发 pre-commit，lint-staged 对暂存文件跑 Prettier，再加 typecheck 和 test 脚本。

## 2. 它解决什么问题

提交前的格式化、类型检查、测试靠人自觉不可靠。本 skill 把它们挂进 git hook，让每次 commit 自动跑，坏代码在提交时就拦下。

## 3. 核心心智模型

**四个组件**：Husky（hook 框架）→ `.husky/pre-commit`（触发 lint-staged + typecheck + test）→ `.lintstagedrc`（`*` → `prettier --ignore-unknown --write`）→ `.prettierrc`（若缺则建默认配置）。

**两个注意**：Husky v9+ 的 hook 文件**不需要 shebang**；`prettier --ignore-unknown` 跳过 Prettier 解析不了的文件（图片等）。

## 4. 一次典型运转

1. 探包管理器（package-lock/pnpm-lock/yarn.lock/bun.lockb，默认 npm）。
2. 装 husky + lint-staged + prettier（devDependencies）。
3. `npx husky init`。
4. 写 `.husky/pre-commit`（适配包管理器；无 typecheck/test 脚本则省略对应行并告知）。
5. 写 `.lintstagedrc`。
6. 缺 Prettier 配置才建 `.prettierrc`。
7. 验证。
8. 提交（顺带 smoke test 新钩子）。

## 5. 何时用 / 何时不用

**用**：想加 pre-commit hooks、装 Husky、配 lint-staged、加提交时格式化/类型检查/测试时。

**不用**：不需要提交前自动检查的仓库。

## 6. 依赖与网络位置

- 依赖 husky、lint-staged、prettier。
- 与 `git-guardrails-claude-code`（安全拦截）互补：一个是"拦危险命令"，一个是"提交前检查"。

## 7. 易错点与坑

- **给 Husky v9+ hook 加 shebang**：不需要。
- **忽略无 typecheck/test 脚本的仓库**：要省略对应行并告知用户。
- **已有 Prettier 配置还覆盖**：只在缺失时才建 `.prettierrc`。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/misc/setup-pre-commit/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
