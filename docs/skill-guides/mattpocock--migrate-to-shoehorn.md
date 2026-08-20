# migrate-to-shoehorn

> 把测试文件里的 `as` 类型断言迁移到 `@total-typescript/shoehorn`，用类型安全的替代。

## 1. 一句话理解

`migrate-to-shoehorn` 把测试里 `as Type` / `as unknown as Type` 换成 shoehorn 的 `fromPartial()` / `fromAny()`，让你能在测试里传**部分数据**（或故意错误的数据）的同时保持 TypeScript 类型安全。

## 2. 它解决什么问题

`as` 断言在测试里有三个毛病：被训练成"别用"、要手写目标类型、故意传错数据还得 `as unknown as Type` 双重断言。对一个只关心 2 个字段、却有 22 个字段的大对象，`as` 逼你伪造全部 22 个。shoehorn 让你只传关心的部分。

## 3. 核心心智模型

**三种映射**：

| 函数 | 用途 |
| --- | --- |
| `fromPartial()` | 传部分数据但仍类型检查（替代 `as Type`） |
| `fromAny()` | 传故意错误的数据（保留自动补全，替代 `as unknown as Type`） |
| `fromExact()` | 强制完整对象（之后可换回 fromPartial） |

**只用于测试代码，绝不用在生产代码。**

## 4. 一次典型运转

1. 收集需求：哪些测试文件有 `as` 问题、是不是大对象只关心部分字段、要不要故意传错数据。
2. 安装 `npm i @total-typescript/shoehorn`。
3. `grep -r " as [A-Z]" --include="*.test.ts" --include="*.spec.ts"` 找断言。
4. `as Type` → `fromPartial()`，`as unknown as Type` → `fromAny()`，加 import。
5. 跑类型检查验证。

## 5. 何时用 / 何时不用

**用**：用户提 shoehorn、想替换测试里的 `as`、或需要部分测试数据时。

**不用**：生产代码（明确禁止）；非测试文件里的 `as`。

## 6. 依赖与网络位置

- 依赖 `@total-typescript/shoehorn`。
- mattpocock 系 skill，与其工程/测试 skill 同源。

## 7. 易错点与坑

- **用进生产代码**：明确禁止，shoehorn 是测试专用。
- **映射搞反**：`as Type`→`fromPartial`，`as unknown as`→`fromAny`，别混。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/misc/migrate-to-shoehorn/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
