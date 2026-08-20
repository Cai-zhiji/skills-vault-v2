# wizard

> 生成一个交互式 bash 向导，带人类一步步走完只有他能做的操作：配基础设施、设凭据/CI secret、走陌生的第三方后台、跑一次性迁移或切换。

## 1. 一句话理解

`wizard` 产出一个**bash 脚本**，把"只有人类能完成、但手做很烦、每次都要给 AI 重新解释一遍"的过程，变成一步步引导：打开 URL、说清点什么点、捕获值、写到 `.env`/GitHub secret、每步确认、显示还剩几步。

## 2. 它解决什么问题

有些步骤 agent 自己做不了——要在第三方后台点按钮、要扫码、要输入只有人类有的凭据。`wizard` 把这类"人肉流程"固化成可复用脚本，让人类跟着走、值自动落到该落的地方，而不是每次口头口述。

## 3. 核心心智模型

**你的活只是"定范围 + 写阶段"，模板已把 UX 全解决了。** `template.sh` 里 `STAGES` 标记之上是一段**完全一致、绝不许手改**的库（分阶段进度、确认门、跨平台开 URL 含 WSL、隐藏 secret 输入、幂等 `.env` upsert、`gh secret`/`gh variable` 写入、结尾总结）。你只需在 `STAGES` 下面写一个个 `stage`。

**wizard 默认是临时的**：为一次运行而建，用完删；只有用户要可复用设置路径时才提交。

## 4. 一次典型运转

1. **定范围**：读仓库（`.env.example`、workflows 里每个 `secrets.*`/`vars.*` 引用都是一个要产出的值），列出有序阶段和每阶段产出的值，和用户确认。
2. **画每段的旅程**：精确到"Dashboard → Developers → API keys → Reveal → copy"，不知道当前 UI 就查文档或问，别编。
3. **写向导**：拷 `template.sh`，换 example stage，用库的 helper（`stage`/`open_url`/`ask_secret`/`write_env`/`set_secret`/`confirm`），设 `TOTAL_STAGES`。
4. **验证交接**：`bash -n` + `shellcheck`，`chmod +x`；**不端到端跑**（会开浏览器阻塞），改静态追踪每个值是否落到该落处；告诉用户怎么跑。

## 5. 何时用 / 何时不用

**用**：配基础设施、设凭据/CI secret、走陌生第三方后台、跑一次性迁移/切换。

**不用**：agent 自己能做的步骤——别为了它造向导。

## 6. 依赖与网络位置

- 依赖 `template.sh`（内置的库）。
- 是 `ask-matt` 提及的独立任务入口之一。

## 7. 易错点与坑

- **手改 `STAGES` 之上的库**：一致性就是要点，绝不许改。
- **端到端跑自己写的向导**：会开浏览器阻塞人类，只能静态追踪。
- **编造不存在的步骤**：当前 UI/命令不确定就查，别发明。
- **为 agent 自己能做的事造向导**：明确禁止。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/engineering/wizard/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
