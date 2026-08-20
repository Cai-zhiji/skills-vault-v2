import type { SelectionMode } from "@/types/api"

export function selectionKey(value: Record<string, SelectionMode>): string {
  return JSON.stringify(
    Object.entries(value)
      .filter(([, mode]) => mode !== "off")
      .sort(([left], [right]) => left.localeCompare(right)),
  )
}

export function availableModes(platforms: string[]): SelectionMode[] {
  const supported = new Set(platforms)
  const modes: SelectionMode[] = ["off"]
  if (supported.has("codex") && supported.has("claude")) modes.push("both")
  if (supported.has("codex")) modes.push("codex")
  if (supported.has("claude")) modes.push("claude")
  return modes
}
