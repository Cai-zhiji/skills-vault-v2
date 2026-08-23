# 跨平台桌面化实施计划

## 里程碑 1：可移植领域核心

- [x] 1.1 建立平台与路径适配层
  - 新增 `AppPaths` 与 `PlatformAdapter`，统一 OS、架构、Agent 目录和可执行文件发现。
  - 移除按 `/` 字符串识别平台和散布的 `Path.home()` 目标目录拼接。
  - 使用伪造平台覆盖 macOS、Windows、Linux 路径测试。
  - _需求：R1、R3、R4_

- [x] 1.2 建立可替换 Skill 部署器
  - 实现 symlink 与 managed-copy 的 plan/apply/verify/remove。
  - 将安装状态升级为 deployments schema，并兼容读取旧 links。
  - 目标被用户修改时阻止覆盖和删除。
  - _需求：R4、R8_

## 里程碑 2：Vault 生命周期与迁移

- [x] 2.1 实现 Vault schema 与初始化服务
  - 增加最小 Vault 模板、schema 版本和新建 Preview/Apply。
  - Git 缺失时仍能创建；Git 初始化作为独立可选动作。
  - _需求：R3、R5、R9_

- [x] 2.2 实现候选目录识别与普通仓库导入
  - 只读识别完整 Vault、Git Skills 仓库、普通 Skills 文件夹和无效目录。
  - 支持“作为来源”和“作为我的 Skills”两种 Preview/Apply。
  - 覆盖冲突、嵌套 Skill、非 ASCII 路径和失败回滚。
  - _需求：R3、R9_

- [x] 2.3 实现 Web v2 Vault 迁移
  - 复制事实数据和来源历史，过滤运行状态，历史记录标记 legacy。
  - 重建 Catalog、核对 Skill ID/指纹，并保持旧 Vault 不变。
  - 平台部署重指向沿用独立安装 Preview/Apply。
  - _需求：R3、R4、R9_

- [x] 2.4 补齐原创 Skill 创建预览
  - 创建向导显示目标、模板、平台和冲突，Apply 后记录事务。
  - 保留现有创建 API 的兼容期，并逐步切换前端。
  - _需求：R9_

## 里程碑 3：可选依赖中心

- [ ] 3.1 实现依赖检测服务
  - 离线检测 Git、Node/npm/npx 和安装提供者。
  - 功能调用缺失依赖时返回结构化 `dependency_missing`。
  - _需求：R5_

- [ ] 3.2 实现受控安装计划
  - 支持 WinGet、已存在的 Homebrew 和 Linux 指令引导。
  - 自动执行必须 Preview/Apply、命令白名单、事务记录且不静默提权。
  - _需求：R5、R8_

- [ ] 3.3 增加依赖中心界面
  - 展示状态、版本、影响能力、安装/打开官方说明和重新检测。
  - 在来源操作附近提供上下文修复入口。
  - _需求：R5_

## 里程碑 4：首次启动桌面体验

- [ ] 4.1 实现首次启动向导
  - 提供创建、打开、导入、迁移 Web v2 四个入口。
  - 显示扫描结果、Preview/Apply 进度、失败恢复和最终 Vault 路径。
  - _需求：R3、R9_

- [ ] 4.2 分离桌面配置、资源和 Vault 数据
  - 应用配置只保存最近 Vault 与桌面设置；事实数据全部留在 Vault。
  - 升级或卸载应用不触碰 Vault。
  - _需求：R3_

## 里程碑 5：Tauri 与 sidecar

- [ ] 5.1 建立 Tauri v2 桌面壳
  - 接入现有 React 构建、最小权限、单实例和窗口生命周期。
  - _需求：R2、R6_

- [ ] 5.2 实现 Python sidecar 运行模式
  - 支持随机回环端口、JSON 握手、会话 token、优雅关闭和父子进程绑定。
  - 浏览器诊断模式保持兼容。
  - _需求：R2、R6、R8_

- [ ] 5.3 接入桌面前端运行配置
  - 前端根据 Tauri 注入配置连接 sidecar，并处理启动、会话和崩溃错误。
  - 收紧 CSP 与 Origin 白名单。
  - _需求：R2、R6_

## 里程碑 6：开发与打包

- [ ] 6.1 建立统一开发入口
  - 根目录提供 `npm run dev`、`dev:web`、`test:all`。
  - 使用跨平台进程编排替代 Bash 作为默认入口。
  - _需求：R1、R8_

- [ ] 6.2 建立 Python sidecar 打包
  - 使用 PyInstaller 生成当前平台 sidecar并按 target triple 命名。
  - 打包前验证测试、版本和所需工具链。
  - _需求：R2、R7_

- [ ] 6.3 建立 Tauri 安装包输出
  - 实现 `npm run package` 和版本化产物目录、校验和与构建元数据。
  - 配置 macOS app/DMG、Windows NSIS、Ubuntu AppImage。
  - _需求：R7_

## 里程碑 7：三平台验收与交付

- [ ] 7.1 当前 macOS 回归与安装包验收
  - 验证创建、Web v2 迁移、平台同步、恢复和卸载数据保留。
  - _需求：R7、R8、R9_

- [ ] 7.2 Windows 原生验收
  - 验证非管理员安装、managed-copy、中文/空格路径和缺失依赖。
  - _需求：R4、R5、R7、R8_

- [ ] 7.3 Ubuntu AppImage 验收
  - 验证启动、路径、权限、缺失依赖和卸载数据保留。
  - _需求：R5、R7、R8_

- [ ] 7.4 更新默认入口与迁移文档
  - README 以桌面安装和 `npm run dev` 为主，旧 Bash 入口标记兼容状态。
  - 记录签名/公证状态和未完成的平台限制。
  - _需求：R1、R7、R9_
