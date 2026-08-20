# wait-what

> 停。上一条消息没讲清楚——重新表述一遍。

## 1. 一句话理解

`wait-what` 是一个**兜底信号**：当 agent 没跟上你的意思，触发它让 agent 停下来，用一点上下文、ASD-STE100 简化技术英语、以及 `CONTEXT.md` 里的统一语言，把刚才的意思重新说清楚。

## 2. 它解决什么问题

对话跑偏、术语对不上时，最省事的是喊停重来，而不是继续在误解上叠新信息。`wait-what` 就是这个"停，重新说"的明确指令。

## 3. 核心心智模型

**用受控语言重新对齐。** 三个要求：给一点上下文、用 ASD-STE100（简化技术英语）表达、用 `CONTEXT.md` 的统一语言（ubiquitous language）说话——用领域术语表里的词，避免各自为政的表述。

## 4. 一次典型运转

用户发现 agent 理解偏了 → `/wait-what` → agent 停下，用 `CONTEXT.md` 术语 + 简化语言把当前理解重述 → 对齐后继续。

## 5. 何时用 / 何时不用

**用**：上一条消息没落地、理解跑偏、术语对不上时。

**不用**：一切都清楚、只是要继续推进时。

## 6. 依赖与网络位置

- 依赖 `CONTEXT.md`（若有）。
- 是 productivity 里极简的纠偏工具。

## 7. 易错点与坑

- **别当常规指令用**：它是纠偏信号，不是推进工具。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/productivity/wait-what/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
