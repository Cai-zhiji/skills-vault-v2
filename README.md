# Skills Vault v2

Copyright (c) 2026 Cai-zhiji

本项目采用 [GNU Affero General Public License v3.0 or later](LICENSE)。你可以自由使用、研究、修改和再分发本项目；基于本项目提供网络服务时，也必须向用户提供对应的源代码。项目中的用户 Vault、原创 Skill、备份和说明文档属于用户数据，不会因应用卸载或升级而被删除。

本地优先的 Agent Skills 桌面管理工作台。正式入口采用 Tauri v2，React 界面负责浏览与操作，Python sidecar 负责 Vault、Catalog、来源、平台部署、事务与恢复。Git 和外部 Skills CLI 都是可选增强能力，不影响应用启动和原创 Skill 管理。

## 用户如何开始

安装并打开 Skills Vault 后，首次启动提供四种入口：

- **创建新 Vault**：适合没有 Skills 仓库的用户；创建后可在 Skills 页面通过“创建 Skill”建立自己的 Skill。
- **打开已有 Vault**：适合已经由桌面版创建或迁移完成的 Vault。
- **导入 Skills 文件夹**：把普通仓库或文件夹中的 `SKILL.md` 扫描后复制到新 Vault 的“我的 Skills”，原目录不变。
- **迁移旧版 Web Vault**：复制旧项目中的事实数据与来源历史，过滤运行缓存，并重建 Catalog；旧项目保留为回滚副本。

完整说明见 [Vault 初始化与迁移指南](docs/guides/desktop-vault-migration.md)。

## 开发者快速启动

环境要求：Node.js 20+、npm、Python 3.9+、Rust 1.77.2+。先安装依赖：

```bash
npm install
npm --prefix app ci
```

之后一条命令启动 Tauri 桌面开发模式：

```bash
npm run dev
```

如果暂未安装 Rust，可使用浏览器诊断模式：

```bash
npm run dev:web
```

旧的 `./scripts/vault-ui` 与 `./scripts/skills` 暂时保留为兼容入口，不再是默认开发或分发方式。

## 验证与打包

```bash
npm run test:all
npm run package:diagnose
npm run package
```

`npm run package` 会检查工具链、运行全部测试、在项目本地 `.venv-build` 安装固定版本的 PyInstaller、生成当前平台 sidecar，再调用 Tauri 输出安装包、校验和与构建元数据。产物位于 `dist/packages/<version>/<platform>-<arch>/`。

PyInstaller 不能跨操作系统构建，因此 macOS `.app/.dmg`、Windows NSIS 与 Ubuntu AppImage 必须分别在对应系统执行。未经开发者身份签名或公证的产物只用于内部测试；公开分发前仍需完成 macOS Developer ID 签名与公证或 Windows 代码签名。

## 主要能力

- **Skills**：浏览、搜索、按来源和状态筛选，创建原创 Skill，保存 Codex / Claude Code 启用范围，并通过 Preview 安全部署。
- **来源**：管理 Git、Skills CLI 与本地复制来源；缺少外部环境时展示影响和安装入口。
- **记录**：追踪事务、更新报告和备份，并在恢复前生成一次性 Preview。
- **跨平台部署**：macOS/Linux 默认受管链接，Windows 默认受管复制；目标被用户修改时阻止覆盖或删除。
- **桌面安全**：sidecar 使用随机端口、进程内会话令牌、严格 Origin 和父进程生命周期绑定。

## 数据与安全边界

- Vault 是用户选择的独立数据目录；应用配置只保存最近 Vault 和桌面状态，升级或卸载不删除 Vault。
- `registry.yaml`、`lock.yaml`、`profiles/`、`annotations/`、`my-skills/` 与 `docs/skill-guides/` 是事实数据。
- `sources/` 保留各来源自己的历史；`catalog/` 是可重建索引，`.vault/` 保存本机事务、备份和部署状态。
- 写操作遵循 `preview → apply → transaction → recovery`；用户原创和上游内容不得被静默覆盖或删除。
- 项目只使用本地 Git，不自动 push。

产品规格见 [桌面化需求](docs/specs/cross-platform-desktop/requirements.md)、[技术设计](docs/specs/cross-platform-desktop/design.md) 与 [实施任务](docs/specs/cross-platform-desktop/tasks.md)。
