# 骨架 — 按功能域一层管理

```
.
├── CLAUDE.md            # 精简指针（Claude 自动加载）
├── AGENTS.md            # 精简指针（Codex 自动加载）
├── CONTEXT.md           # 领域词汇表
├── docs/
│   ├── STATUS.md        # 状态 + 进度 + 下一步
│   ├── adr/             # 决策记录
│   ├── devlog/          # 开发日志（每会话一篇）
│   ├── api/             # API 设计文档
│   └── specs/           # spec 文档（to-spec 输出）
├── design/
│   ├── ui/              # 设计稿 / 规范
│   ├── prototype/       # 交互原型
│   └── assets/          # 静态素材
├── database/
│   ├── schema/          # DDL / 迁移
│   └── seeds/           # 种子数据
├── scripts/             # 构建 / 部署 / 开发脚本
├── ops/                 # Docker / CI / env 模板
├── app/                 # 前端代码（脚手架生成，不预填）
└── server/              # 后端代码（脚手架生成，不预填）
```

## 建法
- 所有空目录放 `.gitkeep` — 它们宣告规划好的域，**永不清理**。
- `app/` `server/` 只建目录，**不放任何内容** — 框架脚手架（Vite/Next/Taro…）决定它们内部结构。
- 测试放在 `app/` `server/` 各自的 `tests/`（随脚手架），不是顶层域。
