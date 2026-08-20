# 批量管理 Skills

## 背景

Skills 页面原先只能逐项调整启用范围或逐项打开删除入口。面对几十个 Skill，重复操作成本高，也容易漏选或误操作。

## 实现

- 在 Catalog 列表增加逐项复选框与“选择当前结果”全选入口。
- 增加批量工具栏，显示当前选择数量。
- 支持对选中项批量设置“全部关闭 / 两端启用 / 仅 Codex / 仅 Claude”；不支持所有选中项的平台范围会被禁用。
- 支持批量删除或移出，并复用现有 `skill.delete` 多项 Preview / Apply 事务，先展示受影响的 Skill、说明文档、配置文件和平台链接。
- 保持筛选条件不变；全选只作用于当前筛选结果，跨筛选已选项不会被静默清除。

## 验收

- `npm run typecheck`、`npm run lint`、`npm run build` 通过。
- `PYTHONPATH=server python3 -m unittest server/test_core.py`：38 个测试通过，8 个跳过。
- 浏览器验证 `/skills`：桌面端多选、批量范围菜单、批量删除影响预览；390px 窄屏选择状态；无新增控制台错误。
- 未在真实数据上确认“批量删除 / 移出”，仅验证 Preview，避免验收动作改变用户数据。
