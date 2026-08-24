import { lazy, Suspense } from "react"
import { Navigate, Route, Routes } from "react-router-dom"

import { AppShell } from "@/components/app-shell"
import { DesktopGate } from "@/components/desktop-gate"

const SkillsPage = lazy(() =>
  import("@/pages/skills-page").then((module) => ({ default: module.SkillsPage })),
)
const SourcesPage = lazy(() =>
  import("@/pages/sources-page").then((module) => ({ default: module.SourcesPage })),
)
const RecordsPage = lazy(() =>
  import("@/pages/records-page").then((module) => ({ default: module.RecordsPage })),
)
const SettingsPage = lazy(() =>
  import("@/pages/settings-page").then((module) => ({ default: module.SettingsPage })),
)
const HelpPage = lazy(() =>
  import("@/pages/help-page").then((module) => ({ default: module.HelpPage })),
)
const AboutPage = lazy(() =>
  import("@/pages/about-page").then((module) => ({ default: module.AboutPage })),
)

function PageFallback() {
  return (
    <div className="empty-state" aria-live="polite">
      <p className="eyebrow">LOADING WORKSPACE</p>
      <h2>正在装载工作台</h2>
    </div>
  )
}

export default function App() {
  return (
    <DesktopGate>
      <Suspense fallback={<PageFallback />}>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<Navigate to="/skills" replace />} />
            <Route path="skills" element={<SkillsPage />} />
            <Route path="sources" element={<SourcesPage />} />
            <Route path="records" element={<RecordsPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="help" element={<HelpPage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="*" element={<Navigate to="/skills" replace />} />
          </Route>
        </Routes>
      </Suspense>
    </DesktopGate>
  )
}
