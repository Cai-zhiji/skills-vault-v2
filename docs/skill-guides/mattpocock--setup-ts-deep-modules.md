# setup-ts-deep-modules

> 把 dependency-cruiser 接进 TypeScript 仓库，让每个 package 成为"深模块"——实现藏在子文件夹，只能通过入口文件触达。

## 1. 一句话理解

`setup-ts-deep-modules` 装 dependency-cruiser 并写 4 条规则，强制每个 package 的公共面 = 根文件（入口点），子文件夹（`lib/`、`tests/`）对外不可见，然后**证明规则真的会咬人**。

## 2. 它解决什么问题

TS monorepo 里，"包与包之间只能通过公开入口 import"这条纪律靠人守不住——总会有人深 import 进某个包的 `lib/impl`，把实现细节泄漏成事实 API。用 dependency-cruiser 把"深模块"从约定变成 CI 强制。

## 3. 核心心智模型

**入口点是根文件，不是 barrel。** 一个包的公共面是它**所有的根文件**（`index.ts`、`client.ts`、`server.ts`），不是某个指定的 `index.ts`。实现放子文件夹（约定 `lib/`），测试放 `tests/`。**明确劝阻 barrel 文件**——宁要几个小入口点，不要一个 `index.ts` 重导出整棵子树。

**四条规则，全 `error`**：

1. **入口边界**：包外代码只能 import 该包的根文件，不能 import 任何子文件夹。
2. **包内自由**：包自己内部文件互相 import 自由。
3. **测试经入口**：`tests/` 下的文件只能 import 任何包的入口点和自己的 `tests/` fixtures，绝不 import 任何包的子文件夹内部（连自己的都不行）。
4. **无环**：无依赖环。

**公有/私有由"深度"决定**：根文件是入口点，子文件夹一律私有；规则不硬编码 `lib/`/`tests/` 名字——任何子文件夹都是私有的，所以新建文件夹永远不用改 config。

## 4. 一次典型运转

1. **探环境**：包管理器（pnpm/yarn/bun/npm）、packages 根（`src/packages` 或 `packages`）、是否已有 `.dependency-cruiser.*`。
2. **装 dependency-cruiser**（devDependency）。
3. **写 config**：拷 `dependency-cruiser.config.cjs` 到根，设 `PACKAGES_ROOT`。
4. **接进检查**：加 `lint:boundaries` 脚本，并进 umbrella check（typecheck 同一条命令）。
5. **建 example 包**：`index.ts`（导出委托给内部文件的函数，可见地"深"）+ `lib/impl.ts`（子文件夹，外不可达）+ `tests/example.test.ts`（只 import `../index`）。
6. **证明规则咬人**（整个 skill 的完成标准）：干净 example 上 `lint:boundaries` 通过 → 临时加一个深 import，必须失败（`tests-through-entrypoints`）→ 还原，再通过。若第 2 步不失败，规则没接对，修好再收工。
7. **写文档**：`<packages-root>/README.md`（布局 + 四规则 + 怎么跑 lint + 劝阻 barrel），并从 `CLAUDE.md`/`AGENTS.md` 加一行上下文指针。

## 5. 何时用 / 何时不用

**用**：想让 TS 仓库的每个包变成深模块、强制"只经入口 import"时。用户显式调用。

**不用**：单包仓库（无 packages 结构）、不想要入口边界强制的仓库。

## 6. 依赖与网络位置

- 依赖 dependency-cruiser。
- 用 `codebase-design` 的词汇（deep module / interface / seam / depth）。
- 附属：`dependency-cruiser.config.cjs`。

## 7. 易错点与坑

- **把 config 的 `$1` 反向引用压平成逐包规则**：`$1` 正是让包能触达自己内部而外人不行的机制，别压平。
- **只接脚本不证明咬人**：规则接好却没验证会咬人 = 白搭，第 6 步是完成标准。
- **用 `.js` 而非 `.cjs`**：`"type": "module"` 仓库里 `.js` 的 `module.exports` 会挂，用 `.cjs`。
- **barrel 化**：劝阻用一个大 index 重导出整棵子树，要几个小入口点。

## 8. 出处

- 原始路径：`sources/mattpocock-skills/skills/in-progress/setup-ts-deep-modules/SKILL.md`
- 上游 commit：`8b78b53`
- 平台兼容：codex、claude（both）
