export type SelectionMode = "off" | "both" | "codex" | "claude"

export interface CatalogState {
  fresh: boolean
  added: string[]
  changed: string[]
  missing: string[]
  personal_skills: number
}

export interface SourceRow {
  id: string
  kind: "git" | "skills-cli" | string
  update_policy: string
  path: string
  skill_root: string
  url: string
  branch: string | null
  trust: string
  license: string
  exists: boolean
  commit: string | null
  locked: string | null
  observed_revision: string | null
  dirty: boolean | null
  enabled: boolean
  remote_commit?: string | null
  remote_url?: string | null
  dirty_files: string[]
  head_modified_at: string | null
  hold: boolean
  pin: string | null
  audit?: Record<string, unknown>
}

export interface StatusPayload {
  root: string
  app_version: string
  generated_at: string | null
  active_profiles: string[]
  catalog: {
    skills: number
    published: number
    conflict_groups: number
    duplicate_ids: number
  }
  conflicts: Record<string, string[]>
  sources: SourceRow[]
  managed_links: number
  last_backup: string | null
  derived_drift: Array<Record<string, unknown>>
  catalog_state: CatalogState
}

export interface DesktopStatusPayload {
  mode: "ready" | "onboarding"
  active_vault: string | null
  configured_vault: string | null
  configured_vault_missing: boolean
  recent_vaults: string[]
  default_vault: string
  config_root: string
}

export interface DesktopOnboardingPreview {
  action: "create" | "open" | "import" | "migrate"
  preview_token: string
  plan: {
    destination?: string
    source?: string
    paths?: string[]
    facts?: string[]
    legacy_history?: string[]
    candidate?: {
      path: string
      kind: string
      skill_count: number
      estimated_bytes: number
      conflicts: Record<string, string[]>
    }
  }
}

export interface DesktopOnboardingResult {
  transaction_id: string
  status: string
  action: string
  active_vault: string
  imported_skills: string[]
}

export interface DesktopLeaveResult {
  transaction_id: string
  status: string
  action: "leave"
  previous_vault: string | null
}

export interface SkillCompatibility {
  level: string
  platforms: string[]
  notes: string[]
}

export interface SkillEntry {
  id: string
  source_id: string
  name: string
  path: string
  source_relative_path: string | null
  source_kind?: string
  description: string
  classification: string
  source_commit: string | null
  upstream_modified_at?: string | null
  local_modified_at?: string | null
  review_status: string
  title_zh: string | null
  summary_zh: string | null
  recommended_for: string[]
  not_recommended_for: string[]
  requires: string[]
  recommends: string[]
  routes_to: string[]
  compatibility: SkillCompatibility
  scripts: string[]
  risk_signals: string[]
  fingerprint: string
  invocation: {
    mode: string
    codex: string
    claude: string
  }
  origin?: Record<string, unknown> | null
}

export interface SkillsPayload {
  total: number
  skills: SkillEntry[]
}

export interface EnablementState {
  selected: boolean
  installed?: boolean
  state: string
  reasons: Array<Record<string, unknown>>
  error?: string
}

export interface SkillDetailPayload extends SkillEntry {
  enablement: {
    codex: EnablementState
    claude: EnablementState
  }
  source: SourceRow | null
  origin_detail: Record<string, unknown> | null
}

export interface DeleteSkillPreview {
  transaction_id: string
  preview_token: string
  skill_ids: string[]
  items: Array<{
    id: string
    name: string
    source_id: string
    path: string
    source_action: string
    guide: string | null
    annotation: boolean
  }>
  profiles: Array<Record<string, unknown>>
  annotation_references: Array<Record<string, unknown>>
  links: Array<Record<string, unknown>>
  derivatives_retained: string[]
  counts: {
    skills: number
    profiles: number
    links: number
    guides: number
    annotations: number
  }
  notes: string[]
}

export interface CompareSkillsResponse {
  left: SkillEntry
  right: SkillEntry
  diff: string[]
  same_name: boolean
}

export interface SkillGuidePayload {
  skill_id: string
  exists: boolean
  editable: boolean
  path: string
  markdown: string
  template: string
}

export interface SaveSkillGuideResponse {
  transaction_id: string
  status: string
  skill_id: string
  path: string
  created: boolean
}

export interface CreateOriginalResponse extends ApplyResponse {
  skill_id: string
  path: string
}

export interface CreateOriginalPreview {
  transaction_id: string
  preview_token: string
  skill_id: string
  name: string
  description: string
  destination: string
  files: string[]
  template: string
}

export interface DependencyRow {
  id: string
  label: string
  status: "available" | "missing" | "outdated" | "broken" | "unverified" | "checking"
  path: string | null
  version: string | null
  capabilities: string[]
  official_url: string
  resolution_source?: string | null
  notes?: string[]
}

export interface DependenciesPayload {
  platform: string
  architecture: string
  dependencies: DependencyRow[]
  installers: Array<{ id: string; path: string }>
  offline: boolean
}

export interface DependencyInstallPreview extends PreviewTokenResponse {
  dependency: string
  label: string
  provider: string | null
  command: string[]
  display_command: string
  can_execute: boolean
  requires_elevation: boolean
  official_url: string
  notes: string[]
}

export interface SourceAddPreview extends PreviewTokenResponse {
  source_id: string
  source_url: string
  source_ref?: string
  input_kind?: string
  kind: string
  dependency?: {
    name: string
    path: string
    resolution_source: string
  }
  skills?: Array<{ name: string; path: string; description: string }> | string[]
  notes?: string[]
}

export interface SelectionPayload {
  active_profiles: string[]
  managed: boolean
  selections: Record<string, SelectionMode>
  resolved: {
    codex: { direct: string[]; effective: string[]; notes: string[] }
    claude: { direct: string[]; effective: string[]; notes: string[] }
  }
  conflicts: Record<string, string[]>
}

export interface ScanResult {
  transaction_id: string
  status: string
  added: string[]
  changed: string[]
  removed: string[]
  conflicts: Record<string, string[]>
  counts: StatusPayload["catalog"]
  catalog_state: CatalogState
}

export interface InstallChange {
  platform: string
  skill_id: string
  name: string
  path: string
  target: string
}

export interface InstallPreview {
  profiles: string[]
  operations: InstallChange[]
  notes: string[]
  changes: {
    added: InstallChange[]
    removed: InstallChange[]
    changed: InstallChange[]
    kept: InstallChange[]
  }
  transaction_id: string
  preview_token: string
}

export interface UpdateSourceRow {
  source_id: string
  source_kind: string
  status: string
  head: string | null
  target: string | null
  branch?: string | null
  target_ref?: string | null
  dirty: boolean
  commits: string[]
  changes: string[]
  risk_signals: string[]
}

export interface UpdatePreview {
  sources: UpdateSourceRow[]
  actionable_source_ids: string[]
  blocked_source_ids: string[]
  preview_token: string
  transaction_id: string
}

export interface TransactionRow {
  transaction_id: string
  created_at: string
  operation: string
  status: string
  [key: string]: unknown
}

export interface BackupRow {
  id: string
  path: string
  created_at: string
}

export interface PreviewTokenResponse {
  preview_token: string
  transaction_id?: string
  [key: string]: unknown
}

export interface ApplyResponse {
  transaction_id: string
  status: string
  [key: string]: unknown
}
