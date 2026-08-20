import { lazy, Suspense } from "react"
import { Navigate, Route, Routes } from "react-router-dom"

import { AppShell } from "@/components/app-shell"

const SkillsPage = lazy(() =>
  import("@/pages/skills-page").then((module) => ({ default: module.SkillsPage })),
)
const SourcesPage = lazy(() =>
  import("@/pages/sources-page").then((module) => ({ default: module.SourcesPage })),
)
const RecordsPage = lazy(() =>
  import("@/pages/records-page").then((module) => ({ default: module.RecordsPage })),
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
    <Suspense fallback={<PageFallback />}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/skills" replace />} />
          <Route path="skills" element={<SkillsPage />} />
          <Route path="sources" element={<SourcesPage />} />
          <Route path="records" element={<RecordsPage />} />
          <Route path="*" element={<Navigate to="/skills" replace />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
