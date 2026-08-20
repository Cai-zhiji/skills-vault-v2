# Skills Vault v2

以网站为主要入口的本地优先 Agent Skills 管理工作台。它把 Skills 浏览与筛选、平台启用范围、来源健康、更新安全、事务和恢复记录放在同一个 React 界面中。

## 快速启动

环境要求：Node.js 20+、npm、Python 3.10+。

```bash
./scripts/vault-ui
```

首次运行会自动安装前端依赖并构建网站，然后在 `http://127.0.0.1:8765` 启动本地服务。默认数据工作区是相邻的 `../skills-vault`；也可以显式指定：

```bash
SKILLS_VAULT_ROOT=/absolute/path/to/skills-vault ./scripts/vault-ui --port 9000
```

## 网站能力

- **Skills**：浏览、搜索、按来源和状态筛选，查看说明与技术信息，保存 Codex / Claude Code 启用范围，并通过 Preview 安全同步。
- **个人说明文档**：为 `my-skills` 中的原创或派生 Skill 添加、编辑标准 8 节 Markdown 说明；文档保存于数据工作区的 `docs/skill-guides/`，不修改 `SKILL.md` 或上游仓库。
- **来源**：查看版本、信任状态和本地改动；更新时自动隔离脏来源，不覆盖用户文件。
- **记录**：追踪事务、更新报告和备份，并在恢复前生成一次性 Preview。
- **同步轨**：持续展示本地 Skills、Catalog 和两个 Agent 平台之间的真实状态。
- **命令面板**：使用 `⌘K` 快速导航和进入常用任务。

## 开发

终端一：

```bash
python3 server/http_server.py --port 8766 --vault-root /absolute/path/to/skills-vault
```

终端二：

```bash
cd app
npm ci
npm run dev
```

Vite 会把 `/api` 代理到 `127.0.0.1:8766`。

## 验证

```bash
cd app
npm run typecheck
npm run lint
npm test
npm run build

cd ..
PYTHONPATH=server python3 -m unittest discover -s server -p 'test_*.py' -v
```

默认后端测试使用临时工作区，不写入相邻的旧项目。只有显式设置 `SKILLS_VAULT_TEST_ROOT` 时，才会运行依赖完整真实数据的集成用例。

## 安全边界

- 服务默认只监听本机地址，并校验写请求来源。
- 批量或破坏性操作采用 `preview → apply → transaction → recovery`。
- 来源存在本地改动时不会被自动清理、暂存、提交或覆盖。
- v2 复用指定的数据工作区，不复制或迁移用户 Skills。
- 个人说明文档是独立的受管 Markdown 文件，每次保存都会产生事务记录。
- 项目只使用本地 Git，不自动推送。

产品规格见 [`docs/specs/skills-vault-v2.md`](docs/specs/skills-vault-v2.md)，视觉方向见 [`design/ui/direction.md`](design/ui/direction.md)。
