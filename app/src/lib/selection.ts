import type { SelectionMode } from "@/types/api"

export const modePlatforms: Record<SelectionMode, string[]> = {
  off: [],
  both: ["codex", "claude"],
  all: ["codex", "claude", "lux"],
  codex: ["codex"],
  claude: ["claude"],
  lux: ["lux"],
  "codex-lux": ["codex", "lux"],
  "claude-lux": ["claude", "lux"],
}

const modeOrder: SelectionMode[] = [
  "off",
  "all",
  "both",
  "codex-lux",
  "claude-lux",
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
