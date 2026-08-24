import { useEffect, useMemo, useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  BookOpenText,
  Boxes,
  Command as CommandIcon,
  DatabaseZap,
  History,
  HelpCircle,
  Library,
  Settings,
  Search,
} from "lucide-react"
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom"

import { OperationRail } from "@/components/operation-rail"
import { FirstRunGuide } from "@/components/first-run-guide"
import { QueryErrorState } from "@/components/query-state"
import { SyncRail } from "@/components/sync-rail"
import { VaultMenu } from "@/components/vault-menu"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandShortcut,
} from "@/components/ui/command"
import { Separator } from "@/components/ui/separator"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"
import { api } from "@/lib/api"
import { useOperation } from "@/lib/operation-context"
import { applyPreferences, readPreferences, type AppPreferences } from "@/lib/preferences"
import { cn } from "@/lib/utils"
import type { SelectionPayload, StatusPayload } from "@/types/api"

const navigation = [
  { to: "/skills", label: "Skills", icon: Boxes, shortcut: "G S" },
  { to: "/sources", label: "来源", icon: DatabaseZap, shortcut: "G O" },
  { to: "/records", label: "记录", icon: History, shortcut: "G R" },
]

const pageMeta: Record<string, { eyebrow: string; title: string; description: string }> = {
  "/skills": {
    eyebrow: "CATALOG / MANAGE",
    title: "Skills",
    description: "浏览、选择并同步到你的 Agent 平台。",
  },
  "/sources": {
    eyebrow: "UPSTREAM / HEALTH",
    title: "来源",
    description: "检查版本、信任状态、本地改动与安全更新。",
  },
  "/records": {
    eyebrow: "TRANSACTIONS / RECOVERY",
    title: "记录",
    description: "追踪写操作、更新报告与可恢复备份。",
  },
  "/settings": {
    eyebrow: "DESKTOP / CONFIGURATION",
    title: "设置",
    description: "管理 Vault、平台和本机运行边界。",
  },
  "/help": {
    eyebrow: "FIELD MANUAL / SUPPORT",
    title: "帮助",
    description: "理解状态、写入边界和恢复路径。",
  },
  "/about": {
    eyebrow: "IDENTITY / BUILD RECORD",
    title: "关于",
    description: "查看应用、运行时和当前工作区信息。",
  },
}

export function AppShell() {
  const location = useLocation()
  const navigate = useNavigate()
  const [commandOpen, setCommandOpen] = useState(false)
  const { operation } = useOperation()
  const [preferences, setPreferences] = useState<AppPreferences>(() => readPreferences())
  const page = pageMeta[location.pathname] || pageMeta["/skills"]
  const statusQuery = useQuery({
    queryKey: ["status"],
    queryFn: () => api.get<StatusPayload>("/api/status"),
    refetchInterval: 30_000,
  })
  const selectionQuery = useQuery({
    queryKey: ["selection"],
    queryFn: () => api.get<SelectionPayload>("/api/selection"),
  })

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault()
        setCommandOpen((open) => !open)
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [])

  useEffect(() => {
    const handleBeforeUnload = (event: BeforeUnloadEvent) => {
      if (operation.state !== "running") return
      event.preventDefault()
      event.returnValue = ""
    }
    window.addEventListener("beforeunload", handleBeforeUnload)
    return () => window.removeEventListener("beforeunload", handleBeforeUnload)
  }, [operation.state])

  useEffect(() => {
    applyPreferences(preferences)
    const handlePreferences = (event: Event) => {
      const custom = event as CustomEvent<AppPreferences>
      setPreferences(custom.detail)
    }
    window.addEventListener("skills-vault-preferences", handlePreferences)
    return () => window.removeEventListener("skills-vault-preferences", handlePreferences)
  }, [preferences])

  const workspaceName = useMemo(() => {
    const root = statusQuery.data?.root
    return root ? root.split("/").filter(Boolean).at(-1) : "连接中"
  }, [statusQuery.data?.root])

  const runCommand = (path: string) => {
    navigate(path)
    setCommandOpen(false)
  }

  return (
    <div className="app-grid">
      <aside className="sidebar-shell">
        <div className="brand-lockup">
          <div className="brand-mark" aria-hidden="true">
            <Library className="size-4" />
          </div>
          <div className="min-w-0">
            <p className="font-label text-base leading-none tracking-wide">Skills Vault</p>
            <p className="mt-1 truncate font-data text-[9px] text-muted-foreground">
              {workspaceName} / local
            </p>
          </div>
        </div>

        <div className="sidebar-vault-menu">
          <VaultMenu />
        </div>

        <nav className="primary-nav" aria-label="主要导航">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn("primary-nav-link", isActive && "primary-nav-link-active")
                }
              >
                <Icon aria-hidden="true" />
                <span>{item.label}</span>
                <span className="ml-auto font-data text-[9px] opacity-45">
                  {item.shortcut}
                </span>
              </NavLink>
            )
          })}
        </nav>

        <div className="sidebar-meta">
          <Separator />
          <div className="space-y-2 px-3 py-4">
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-muted-foreground">Catalog</span>
              <span className="font-data">
                {statusQuery.data?.catalog.skills ?? "—"}
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-muted-foreground">Managed links</span>
              <span className="font-data">
                {statusQuery.data?.managed_links ?? "—"}
              </span>
            </div>
            <div className="flex items-center justify-between text-[11px]">
              <span className="text-muted-foreground">Version</span>
              <span className="font-data">
                {statusQuery.data?.app_version || "2.0.0"}
              </span>
            </div>
          </div>
        </div>
      </aside>

      <div className="main-shell">
        <header className="topbar">
          <div className="mobile-vault-menu"><VaultMenu /></div>
          <div className="min-w-0">
            <p className="eyebrow">{page.eyebrow}</p>
            <div className="mt-1 flex items-baseline gap-3">
              <h1 className="font-label text-2xl leading-none tracking-wide">
                {page.title}
              </h1>
              <p className="hidden truncate text-xs text-muted-foreground md:block">
                {page.description}
              </p>
            </div>
          </div>
          <Tooltip>
            <TooltipTrigger
              render={
                <Button
                  variant="outline"
                  className="command-trigger"
                  onClick={() => setCommandOpen(true)}
                />
              }
            >
              <Search />
              <span className="hidden sm:inline">快速打开</span>
              <kbd>⌘K</kbd>
            </TooltipTrigger>
            <TooltipContent>打开全局命令</TooltipContent>
          </Tooltip>
          <div className="hidden items-center gap-1 md:flex">
            <Tooltip><TooltipTrigger render={<Button variant="ghost" size="icon" aria-label="打开帮助" onClick={() => navigate("/help")} />}><HelpCircle /></TooltipTrigger><TooltipContent>使用帮助</TooltipContent></Tooltip>
            <Tooltip><TooltipTrigger render={<Button variant="ghost" size="icon" aria-label="打开设置" onClick={() => navigate("/settings")} />}><Settings /></TooltipTrigger><TooltipContent>设置</TooltipContent></Tooltip>
            <Tooltip><TooltipTrigger render={<Button variant="ghost" size="icon" aria-label="打开关于" onClick={() => navigate("/about")} />}><BookOpenText /></TooltipTrigger><TooltipContent>关于</TooltipContent></Tooltip>
          </div>
        </header>

        <nav className="mobile-nav" aria-label="移动端导航">
          {navigation.map((item) => {
            const Icon = item.icon
            return (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn("mobile-nav-link", isActive && "mobile-nav-link-active")
                }
              >
                <Icon />
                {item.label}
              </NavLink>
            )
          })}
        </nav>

        <main className="content-shell">
          {statusQuery.isError || selectionQuery.isError ? <QueryErrorState message="工作台状态暂时无法读取" onRetry={() => { void statusQuery.refetch(); void selectionQuery.refetch() }} /> : null}
          {location.pathname === "/skills" && !statusQuery.isError && !selectionQuery.isError ? <FirstRunGuide /> : null}
          <div className="mobile-sync-rail">
            <SyncRail
              status={statusQuery.data}
              selection={selectionQuery.data}
              loading={statusQuery.isLoading}
            />
          </div>
          <Outlet />
        </main>
      </div>

      <aside className="context-rail">
        <SyncRail
          status={statusQuery.data}
          selection={selectionQuery.data}
          loading={statusQuery.isLoading}
        />
        <div className="mt-auto">
          <OperationRail />
        </div>
      </aside>

      <CommandDialog
        open={commandOpen}
        onOpenChange={setCommandOpen}
        title="Skills Vault 命令"
        description="快速打开页面和常用任务"
        className="command-dialog"
      >
        <Command>
          <CommandInput placeholder="输入页面或动作…" />
          <CommandList>
            <CommandEmpty>没有匹配的命令</CommandEmpty>
            <CommandGroup heading="前往">
              {navigation.map((item) => {
                const Icon = item.icon
                return (
                  <CommandItem key={item.to} onSelect={() => runCommand(item.to)}>
                    <Icon />
                    {item.label}
                    <CommandShortcut>{item.shortcut}</CommandShortcut>
                  </CommandItem>
                )
              })}
            </CommandGroup>
            <CommandGroup heading="工作台">
              <CommandItem onSelect={() => runCommand("/skills?action=scan")}> 
                <Library />
                扫描本地 Skills
              </CommandItem>
              <CommandItem onSelect={() => runCommand("/sources?action=updates")}> 
                <DatabaseZap />
                检查来源更新
              </CommandItem>
              <CommandItem onSelect={() => runCommand("/records")}> 
                <BookOpenText />
                查看事务和备份
              </CommandItem>
            </CommandGroup>
            <CommandGroup heading="应用">
              <CommandItem onSelect={() => runCommand("/help")}><HelpCircle />使用帮助</CommandItem>
              <CommandItem onSelect={() => runCommand("/settings")}><Settings />设置</CommandItem>
              <CommandItem onSelect={() => runCommand("/about")}><BookOpenText />关于 Skills Vault</CommandItem>
            </CommandGroup>
          </CommandList>
        </Command>
      </CommandDialog>

      <Button
        className="sr-only"
        aria-label="打开命令面板"
        onClick={() => setCommandOpen(true)}
      >
        <CommandIcon />
      </Button>
    </div>
  )
}
