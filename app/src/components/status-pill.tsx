import { AlertTriangle, Check, CircleDashed, LoaderCircle } from "lucide-react"

import { cn } from "@/lib/utils"

export type SemanticStatus = "safe" | "warning" | "fault" | "running" | "muted"

const styles: Record<SemanticStatus, string> = {
  safe: "border-[var(--safe)]/25 bg-[var(--safe)]/10 text-[var(--safe)]",
  warning:
    "border-[var(--copper)]/30 bg-[var(--copper)]/10 text-[var(--copper-deep)]",
  fault: "border-[var(--fault)]/25 bg-[var(--fault)]/10 text-[var(--fault)]",
  running:
    "border-[var(--copper)]/30 bg-[var(--copper)]/10 text-[var(--copper-deep)]",
  muted: "border-border bg-muted/60 text-muted-foreground",
}

const icons = {
  safe: Check,
  warning: AlertTriangle,
  fault: AlertTriangle,
  running: LoaderCircle,
  muted: CircleDashed,
}

export function StatusPill({
  status,
  children,
  className,
}: {
  status: SemanticStatus
  children: React.ReactNode
  className?: string
}) {
  const Icon = icons[status]
  return (
    <span
      className={cn(
        "inline-flex h-6 items-center gap-1.5 rounded-sm border px-2 font-data text-[11px] font-medium",
        styles[status],
        className,
      )}
    >
      <Icon
        aria-hidden="true"
        className={cn("size-3", status === "running" && "animate-spin")}
      />
      {children}
    </span>
  )
}
