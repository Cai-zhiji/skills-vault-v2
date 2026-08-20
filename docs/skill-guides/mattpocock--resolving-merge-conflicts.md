# resolving-merge-conflicts

> 解决进行中的 git merge/rebase 冲突：查状态 → 找每处冲突的一手来源 → 逐块解决 → 跑检查 → 完成合并。

## 1. 一句话理解

`resolving-merge-conflicts` 是一套五步的冲突解决流程，核心原则是**理解双方意图再动手，绝不 `--abort`，绝不发明新行为**。

## 2. 它解决什么问题

解决冲突最大的风险是**按表面行文瞎选一边**，或者嫌烦直接 `--abort` 放弃。本 skill 强制你先读懂每处冲突"为什么改、原意是什么"，再在双方意图上做取舍。

## 3. 核心心智模型

**为每处冲突找一手来源。** 读 commit message、PR、原始 issue/ticket，深挖每个改动背后的意图。然后逐块解决：能兼顾就兼顾，不兼容就选匹配本次合并目标的那一个，并记下取舍——**不要发明新行为**。

## 4. 一次典型运转

1. **看当前状态**：git history + 冲突文件。
2. **找一手来源**：理解每处改动的原意。
3. **逐块解决**：保留双方意图或做明确取舍。
4. **跑自动检查**：通常 typecheck → test → format，修好合并弄坏的东西。
5. **完成**：stage 并 commit；若是 rebase，继续直到所有 commit rebase 完。

## 5. 何时用 / 何时不用

**用**：仓库已经处于 merge 或 rebase 冲突中。

**不用**：还没有冲突、只是预防性讨论合并（这不算）。

## 6. 依赖与网络位置

- 无硬依赖；被 `ask-matt` 提及为独立处理项。
- 与 `code-review`（评审）不同——它只处理"正在发生的冲突"。

## 7. 易错点与坑

- **`--abort` 放弃**：明确禁止——永远解决，不放弃。
- **发明新行为**：只在双方意图里选或兼顾，别自创第三种。
- **不跑检查就提交**：合并可能破坏 typecheck/test，必须验证。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/engineering/resolving-merge-conflicts/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
