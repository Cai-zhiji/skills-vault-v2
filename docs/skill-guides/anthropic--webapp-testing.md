# webapp-testing

> 用 Playwright 测试本地 Web 应用：验证前端、调试 UI、截图、看浏览器日志。

## 1. 一句话理解

`webapp-testing` 用**原生 Python Playwright 脚本**测试本地 Web 应用，配一个 `scripts/with_server.py` 管理服务器生命周期。

## 2. 它解决什么问题

本地 Web 应用的前端功能、UI 行为需要验证时，手动点太慢、纯单测覆盖不到浏览器真实行为。本 skill 用 Playwright 驱动浏览器：截图、查 DOM、断言、看日志。

## 3. 核心心智模型

**决策树选择方法**：

```
用户任务 → 是静态 HTML？
├─ 是 → 直接读 HTML 找 selector → 写 Playwright 脚本
└─ 否（动态）→ 服务器已在跑？
    ├─ 否 → with_server.py 管生命周期 + 简化脚本
    └─ 是 → 侦察-后行动：导航等 networkidle → 截图/查 DOM → 从渲染态找 selector → 用发现的 selector 行动
```

**关键纪律**：脚本**先 `--help` 再跑**，别读源码——这些脚本很大，会污染上下文窗口，当黑盒调用。

## 4. 一次典型运转

静态页面：读 HTML 找 selector → 写 Playwright 断言。动态应用：`with_server.py --help` 起服务器 → 导航等 networkidle → 截图 → 找 selector → 行动。

## 5. 何时用 / 何时不用

**用**：验证前端功能、调试 UI 行为、截图、看浏览器日志。

**不用**：纯后端/非浏览器测试。

## 6. 依赖与网络位置

- 依赖 Playwright。
- 附属：`scripts/with_server.py`。

## 7. 易错点与坑

- **读脚本源码而非黑盒调用**：先 `--help` 跑起来，别读大源码污染上下文。
- **动态页面不等 networkidle**：先等加载完再找 selector。

## 8. 出处

- 原始路径：`sources/anthropic-skills/skills/webapp-testing/SKILL.md`
- 上游 commit：`f17010c`
- 平台兼容：codex、claude（both）
