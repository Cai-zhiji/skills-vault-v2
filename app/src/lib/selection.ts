import type { SelectionMode } from "@/types/api"

export const modePlatforms: Record<SelectionMode, string[]> = {
  off: [],
  both: ["codex", "claude"],
  codex: ["codex"],
  claude: ["claude"],
  lux: ["lux"],
}

const modeOrder: SelectionMode[] = [
  "off",
  "both",
  "codex",
  "claude",
  "lux",
]

export function selectionKey(value: Record<string, SelectionMode>): string {
  return JSON.stringify(
    Object.entries(value)
      .filter(([, mode]) => mode !== "off")
      .sort(([left], [right]) => left.localeCompare(right)),
  )
}

export function availableModes(platforms: string[]): SelectionMode[] {
  const supported = new Set(platforms)
  return modeOrder.filter((mode) =>
    modePlatforms[mode].every((platform) => supported.has(platform)),
  )
}
