export type ThemePreference = "workbench" | "light" | "dark"
export type DensityPreference = "comfortable" | "compact"

export interface AppPreferences {
  theme: ThemePreference
  density: DensityPreference
  reduceMotion: boolean
  shortcuts: boolean
  onboardingDismissed: boolean
  vaultMeta: Record<string, { alias?: string; favorite?: boolean; tags?: string[] }>
}

const STORAGE_KEY = "skills-vault.preferences.v1"

export const defaultPreferences: AppPreferences = {
  theme: "workbench",
  density: "comfortable",
  reduceMotion: false,
  shortcuts: true,
  onboardingDismissed: false,
  vaultMeta: {},
}

export function readPreferences(): AppPreferences {
  if (typeof window === "undefined") return defaultPreferences
  try {
    const parsed: unknown = JSON.parse(localStorage.getItem(STORAGE_KEY) || "null")
    if (!parsed || typeof parsed !== "object") return defaultPreferences
    return { ...defaultPreferences, ...(parsed as Partial<AppPreferences>) }
  } catch {
    return defaultPreferences
  }
}

export function writePreferences(next: AppPreferences): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
  window.dispatchEvent(new CustomEvent("skills-vault-preferences", { detail: next }))
}

export function updatePreferences(patch: Partial<AppPreferences>): AppPreferences {
  const next = { ...readPreferences(), ...patch }
  writePreferences(next)
  return next
}

export function applyPreferences(preferences: AppPreferences): void {
  const root = document.documentElement
  root.dataset.theme = preferences.theme
  root.dataset.density = preferences.density
  root.dataset.reduceMotion = preferences.reduceMotion ? "true" : "false"
}

export function vaultMetaKey(path: string | null | undefined): string {
  return path || "__no_vault__"
}
