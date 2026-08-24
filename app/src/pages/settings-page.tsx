import { useSearchParams } from "react-router-dom"
import { CircleHelp, FolderCog, Laptop, ShieldCheck, SlidersHorizontal, Wrench } from "lucide-react"

const sections = [
  { id: "vault", label: "Vault", icon: FolderCog, title: "Vault 与工作区", description: "管理当前工作区和桌面配置。" },
  { id: "platform", label: "平台", icon: Laptop, title: "Agent 平台", description: "查看 Codex 与 Claude Code 的目标位置。" },
  { id: "dependencies", label: "依赖", icon: ShieldCheck, title: "外部依赖", description: "Git、Node.js 与 Skills CLI 的检测结果位于来源页面。" },
  { id: "diagnostics", label: "诊断", icon: Wrench, title: "诊断与数据", description: "查看运行信息、日志位置和可恢复数据边界。" },
  { id: "appearance", label: "外观", icon: SlidersHorizontal, title: "外观与交互", description: "主题、密度和动态效果设置将在后续版本提供。" },
]

export function SettingsPage() {
  const [params, setParams] = useSearchParams()
  const active = params.get("tab") || "vault"
  const current = sections.find((section) => section.id === active) || sections[0]
  return (
    <div className="page-stack settings-page">
      <section className="settings-intro">
        <div className="settings-intro-copy"><p className="eyebrow">DESKTOP CONFIGURATION</p><h2>设置</h2><p>应用设置只影响本机界面和运行方式，不拥有或覆盖 Vault 中的用户数据。</p></div>
        <div className="settings-intro-aside"><CircleHelp className="settings-intro-mark" /><span>LOCAL / PRIVATE</span></div>
      </section>
      <div className="settings-layout">
        <nav className="settings-nav" aria-label="设置分类">
          <p className="settings-nav-label eyebrow">CONFIG INDEX</p>
          {sections.map((section) => {
            const Icon = section.icon
            return <button key={section.id} type="button" className={active === section.id ? "settings-nav-item settings-nav-item-active" : "settings-nav-item"} onClick={() => setParams({ tab: section.id })}><span className="settings-nav-marker" /><Icon /><span>{section.label}</span></button>
          })}
        </nav>
        <section className="settings-panel">
          <div className="settings-panel-heading"><div><p className="eyebrow">{current.label.toUpperCase()}</p><h3>{current.title}</h3></div><span className="settings-panel-state">DESKTOP</span></div>
          <p className="settings-panel-description">{current.description}</p>
          {active === "vault" ? <div className="settings-note"><strong>当前 Vault 的切换入口在左上角。</strong><span>在那里可以查看路径、打开最近 Vault、重新扫描或退出当前 Vault。退出不会删除任何文件。</span></div> : null}
          {active === "platform" ? <div className="settings-note"><strong>平台目录由系统适配器计算。</strong><span>请在 Skills 页面查看每个 Skill 的实际安装状态，在来源页面检测可选依赖。</span></div> : null}
          {active === "dependencies" ? <div className="settings-note"><strong>依赖中心位于“来源”页面。</strong><span>Git 和 Node.js 缺失时，原创 Skill 的浏览、说明和本地管理仍可继续使用。</span></div> : null}
          {active === "diagnostics" ? <div className="settings-note"><strong>数据边界</strong><span>用户事实数据在 Vault 内；事务、备份和运行缓存由记录页面与本机配置目录分别管理。</span></div> : null}
          {active === "appearance" ? <div className="settings-note"><strong>当前界面遵循系统减少动态效果偏好。</strong><span>主题、密度和语言设置将在偏好存储接入后开放。</span></div> : null}
        </section>
      </div>
    </div>
  )
}
