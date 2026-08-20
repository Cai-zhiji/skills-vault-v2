# web-artifacts-builder

> 用 React + TypeScript + Vite + Tailwind + shadcn/ui 构建复杂的多组件 claude.ai HTML artifact。

## 1. 一句话理解

`web-artifacts-builder` 用现代前端技术栈（React 18 + TS + Vite + Parcel 打包 + Tailwind + shadcn/ui）构建**复杂 artifact**，最后打包成单个 HTML 文件展示。适合需要状态管理、路由或 shadcn/ui 组件的复杂 artifact，不适合简单单文件。

## 2. 它解决什么问题

简单的单文件 HTML 能直接写，但需要状态管理、路由、多个 shadcn/ui 组件、React 生态的复杂 artifact 需要工程化脚手架。本 skill 用 `init-artifact.sh` 建项目、`bundle-artifact.sh` 打成单 HTML，省去手工配置。

## 3. 核心心智模型

**五步流程**：初始化项目（`init-artifact.sh`）→ 开发 → 打包成单 HTML（`bundle-artifact.sh`）→ 展示 → （可选）测试。

**设计风格约束**：避免"AI slop"——不要过度居中布局、紫色渐变、统一圆角、Inter 字体。

## 4. 一次典型运转

`bash scripts/init-artifact.sh <name>` 建项目（React+TS+Vite+Tailwind+shadcn/ui+40+ 组件预装）→ 编辑代码 → `bundle-artifact.sh` 打成单 HTML → 展示给用户。

## 5. 何时用 / 何时不用

**用**：需要状态管理、路由、shadcn/ui 组件的复杂 artifact。

**不用**：简单单文件 HTML/JSX artifact（直接写）。

## 6. 依赖与网络位置

- 附属：`scripts/init-artifact.sh`、`bundle-artifact.sh`。
- 与 `frontend-design`（视觉设计）+ `dataviz` 协同。

## 7. 易错点与坑

- **复杂 artifact 硬写单文件**：需要 React/shadcn 就该用本 skill 脚手架。
- **AI slop 风格**：避免过度居中、紫色渐变、统一圆角、Inter。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/web-artifacts-builder/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
