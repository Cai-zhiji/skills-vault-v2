import { BookOpenText, CircleAlert, GitBranch, LifeBuoy, RotateCcw, ShieldCheck } from "lucide-react"

const topics = [
  { icon: BookOpenText, title: "开始使用", text: "首次启动时可以创建新 Vault、打开已有 Vault、导入 Skills 文件夹，或迁移旧版 Web Vault。" },
  { icon: GitBranch, title: "理解同步轨", text: "本地文件、Catalog、Codex 和 Claude Code 是不同状态。保存选择不等于已经安装到平台。" },
  { icon: ShieldCheck, title: "安全写入", text: "更新、同步、恢复和导入都会先生成 Preview；确认后才会写入，并留下事务和备份记录。" },
  { icon: RotateCcw, title: "恢复与回滚", text: "在记录页面打开备份并预览恢复。来源中的本地改动不会被应用自动整理、提交或覆盖。" },
  { icon: CircleAlert, title: "遇到阻塞", text: "脏来源、同名冲突、分叉更新和受管复制目标被修改时，先按页面提供的差异或修复建议处理。" },
  { icon: LifeBuoy, title: "数据在哪里", text: "Vault 是用户事实数据；应用配置只记录最近 Vault 和桌面状态。升级或卸载应用不会删除 Vault。" },
]

export function HelpPage() {
  return (
    <div className="page-stack help-page">
      <section className="help-hero">
        <div className="help-hero-copy">
          <p className="eyebrow">FIELD MANUAL / LOCAL FIRST</p>
          <h2>使用帮助</h2>
          <p>把 Skills Vault 当作一个本地仓库工作台：先理解状态，再确认写入，最后留下可追踪的记录。</p>
        </div>
        <div className="help-index" aria-label="Skills Vault help manual version">
          <span className="help-index-mark">SV</span>
          <span className="help-index-rule" />
          <span className="help-index-version">02.1 / FIELD NOTES</span>
        </div>
      </section>

      <section className="help-section-heading">
        <div><p className="eyebrow">READ THE WORKBENCH</p><h3>从这里开始</h3></div>
        <p>每一块说明都对应一个你会在工作台中遇到的真实动作。</p>
      </section>

      <section className="help-grid">
        {topics.map(({ icon: Icon, title, text }, index) => (
          <article className="help-topic" key={title}>
            <div className="help-topic-index">0{index + 1}</div>
            <Icon className="help-topic-icon" />
            <div><h3>{title}</h3><p>{text}</p></div>
          </article>
        ))}
      </section>

      <section className="help-faq">
        <div className="help-section-heading"><div><p className="eyebrow">QUICK ANSWERS</p><h3>常见操作</h3></div><p>不确定下一步时，先看这里。</p></div>
        <dl>
          <div><dt>如何切换仓库？</dt><dd>点击左上角当前 Vault 菜单，选择“切换 Vault”或最近使用的 Vault。</dd></div>
          <div><dt>如何退出当前仓库？</dt><dd>在当前 Vault 菜单中选择“退出当前 Vault”。应用会回到选择页，不会删除仓库文件。</dd></div>
          <div><dt>为什么保存后平台还没变化？</dt><dd>保存的是选择状态；还需要在 Skills 页面确认安装 Preview，并应用到对应平台。</dd></div>
        </dl>
      </section>
    </div>
  )
}
