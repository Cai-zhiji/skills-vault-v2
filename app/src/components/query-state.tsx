import { AlertTriangle, RefreshCw } from "lucide-react"

import { Button } from "@/components/ui/button"

export function QueryErrorState({ message = "本地数据暂时无法读取", onRetry }: { message?: string; onRetry: () => void }) {
  return <div className="query-state query-state-error" role="alert"><AlertTriangle /><div><strong>{message}</strong><p>检查本地服务后重试；未确认的写入不会继续执行。</p></div><Button variant="outline" size="sm" onClick={onRetry}><RefreshCw />重试</Button></div>
}

export function QueryEmptyState({ title, description, action }: { title: string; description: string; action?: React.ReactNode }) {
  return <div className="query-state query-state-empty"><div className="query-state-mark">—</div><div><strong>{title}</strong><p>{description}</p></div>{action}</div>
}
