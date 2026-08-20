# qutip

> 开放量子系统仿真：主方程、Lindblad 动力学、退相干、量子光学、腔 QED。

## 1. 一句话理解

`qutip`（Quantum Toolbox in Python）是**量子系统仿真**库，处理封闭（酉）与开放（耗散）量子系统，配多个针对不同场景优化的求解器。

## 2. 它解决什么问题

研究开放量子系统的动力学（主方程、Lindblad 退相干、量子光学、腔 QED）需要专门的量子态/算符表示与时间演化求解器。`qutip` 提供这些，适合物理研究、开放系统动力学、教学仿真。

## 3. 核心心智模型

**量子态 + 算符 + 时间演化。** 快速上手：创建量子态（`basis`）、创建算符（`sigmax` 等）、时间演化（`mesolve`/`sesolve`）、画结果。可选 `qutip-qip`（量子信息处理：电路、门）、`qutip-qtrl`（量子轨迹查看器）。

## 4. 一次典型运转

定义哈密顿量与耗散算符 → 建初态 → `mesolve` 时间演化 → 画布居数/期望值随时间的演化。

## 5. 何时用 / 何时不用

**用**：主方程、Lindblad 动力学、退相干、量子光学、腔 QED、开放系统动力学、教学仿真。

**不用**：**基于电路的量子计算**（量子算法、硬件执行）——用 qiskit/cirq/pennylane。

## 6. 依赖与网络位置

- 是 `scientific-toolkit-skill` 的 embedded 子技能。
- 可选：`qutip-qip`、`qutip-qtrl`。

## 7. 易错点与坑

- **拿它做电路量子计算**：明确不是这个用途，用 qiskit/cirq/pennylane。
- **单位/维度写错**：量子态维度和算符维度要匹配。

## 8. 出处

- 原始路径：`sources/codex-claude-academic-skills/scientific-toolkit-skill/references/scientific-skills/qutip/SKILL.md`
- 上游 commit：`7ed6377`
- 平台兼容：codex、claude（both）
