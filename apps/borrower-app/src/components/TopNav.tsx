import { useEffect, useRef, useState } from "react";
import { Link, NavLink, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles, Search, Plus, Bell, ChevronDown,
  FilePlus2, User2, ScrollText, MessageSquareWarning,
  LogOut, Settings,
} from "lucide-react";
import { Avatar } from "@/components/ui/avatar";
import { cn, formatDateShort } from "@/lib/utils";
import { usePersona } from "@/lib/usePersona";
import { applications, grievances } from "@/lib/mockData";
import { decisionApi } from "@/lib/api";

function getNavForRole(role: string) {
  if (role === "BORROWER") {
    return [
      { to: "/", label: "My Portal", end: true },
      { to: "/consent", label: "My Consents" },
      { to: "/grievances", label: "My Appeals" },
    ];
  }
  if (role === "BANK_SAKHI") {
    return [
      { to: "/", label: "Overview", end: true },
      { to: "/applications/new", label: "Sakhi Entry" },
      { to: "/borrowers", label: "Field Ingest" },
      { to: "/consent", label: "Consent Lookup" },
      { to: "/grievances", label: "Grievances" },
    ];
  }
  if (role === "RISK_OFFICER") {
    return [
      { to: "/", label: "Overview", end: true },
      { to: "/fairness", label: "Fairness Audits" },
      { to: "/models", label: "Model Registry" },
      { to: "/grievances", label: "Grievances" },
    ];
  }
  return [
    { to: "/", label: "Overview", end: true },
    { to: "/applications", label: "Applications" },
    { to: "/fairness", label: "Fairness" },
    { to: "/models", label: role === "ADMIN" ? "Model Registry (Admin)" : "Model Registry" },
    { to: "/grievances", label: "Grievances" },
  ];
}

function getQuickActionsForRole(role: string) {
  if (role === "BORROWER") {
    return [
      { to: "/consent", icon: ScrollText, label: "My consent records", sub: "DPDP hash-chain verification" },
      { to: "/grievances?tab=file", icon: MessageSquareWarning, label: "File score dispute", sub: "168h SLA appeal clock" },
    ];
  }
  return [
    { to: "/applications/new", icon: FilePlus2, label: "New application", sub: "Sakhi entry form" },
    { to: "/borrowers", icon: User2, label: "Aggregate borrower", sub: "Trigger 4-rail ingest" },
    { to: "/consent", icon: ScrollText, label: "Lookup consent", sub: "Verify hash-chain" },
    { to: "/grievances?tab=file", icon: MessageSquareWarning, label: "File grievance", sub: "On behalf of borrower" },
  ];
}

function usePopover<T extends HTMLElement>() {
  const [open, setOpen] = useState(false);
  const ref = useRef<T | null>(null);
  useEffect(() => {
    if (!open) return;
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    function onEsc(e: KeyboardEvent) { if (e.key === "Escape") setOpen(false); }
    document.addEventListener("mousedown", onDoc);
    document.addEventListener("keydown", onEsc);
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);
  return { open, setOpen, ref };
}

export default function TopNav() {
  const persona = usePersona();
  const nav = useNavigate();
  const [q, setQ] = useState("");
  const quick = usePopover<HTMLDivElement>();
  const notif = usePopover<HTMLDivElement>();
  const profile = usePopover<HTMLDivElement>();

  const primaryNav = getNavForRole(persona.role);
  const quickActions = getQuickActionsForRole(persona.role);

  const { data: liveApplications } = useQuery({
    queryKey: ["liveApplicationsNav"],
    queryFn: () => decisionApi.listApplications().catch(() => null),
  });

  const activeApps = (liveApplications && liveApplications.length > 0) ? liveApplications : applications;

  const searchResults = q.trim().length >= 1
    ? activeApps
        .filter((a) =>
          (a.borrower_name || "").toLowerCase().includes(q.toLowerCase()) ||
          (a.id || "").toLowerCase().includes(q.toLowerCase()) ||
          (a.village || "").toLowerCase().includes(q.toLowerCase()) ||
          (a.purpose || "").toLowerCase().includes(q.toLowerCase()),
        )
        .slice(0, 8)
    : [];

  const notifications = [
    ...grievances
      .filter((g) => g.status === "ESCALATED" || (g.status !== "RESOLVED" && g.sla_hours_remaining <= 12))
      .slice(0, 3)
      .map((g) => ({
        id: g.id,
        title: `Grievance ${g.status === "ESCALATED" ? "escalated" : "nearing SLA"}`,
        detail: `${g.borrower_name} · ${g.summary.slice(0, 60)}${g.summary.length > 60 ? "…" : ""}`,
        to: "/grievances",
        tone: "danger" as const,
      })),
    {
      id: "pending",
      title: `${applications.filter((a) => a.decision === "PENDING").length} applications pending review`,
      detail: "Officer decision required within 24h SLA",
      to: "/applications?filter=PENDING",
      tone: "warning" as const,
    },
    {
      id: "gate",
      title: "Fairness gate: PASS",
      detail: "Latest weekly audit — no breaches on ratified manifest v2026.09.01",
      to: "/fairness",
      tone: "success" as const,
    },
  ];

  return (
    <header className="sticky top-0 z-30 px-4 sm:px-6 lg:px-8 pt-4">
      <div className="glass rounded-full px-3 sm:px-4 py-2 flex items-center gap-2 sm:gap-3 max-w-7xl mx-auto">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 pl-1 pr-2">
          <span className="grid place-items-center h-8 w-8 rounded-full bg-primary text-primary-foreground shadow-[0_10px_24px_-8px_rgba(31,55,105,0.55)]">
            <Sparkles className="h-4 w-4" />
          </span>
          <span className="hidden sm:inline font-semibold tracking-tight text-primary">CreditTech</span>
        </Link>

        {/* Primary nav */}
        <nav className="hidden md:flex items-center gap-1 text-sm ml-2">
          {primaryNav.map((n) => (
            <NavLink key={n.to} to={n.to} end={n.end}>
              {({ isActive }) => (
                <span
                  className={cn(
                    "relative inline-flex items-center rounded-full px-3.5 py-1.5 text-muted-foreground",
                    "hover:text-foreground transition-colors",
                    isActive && "text-primary-foreground",
                  )}
                >
                  {isActive && (
                    <motion.span
                      layoutId="topnav-pill"
                      className="absolute inset-0 rounded-full bg-primary shadow-[0_8px_20px_-8px_rgba(31,55,105,0.55)]"
                      transition={{ type: "spring", stiffness: 380, damping: 32 }}
                    />
                  )}
                  <span className="relative">{n.label}</span>
                </span>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Right cluster */}
        <div className="ml-auto flex items-center gap-2">
          {/* Search */}
          <div className="relative hidden lg:block">
            <div className="flex items-center gap-2 bg-white/70 rounded-full px-3.5 py-1.5 border border-white/70 w-64 focus-within:w-80 transition-all">
              <Search className="h-4 w-4 text-muted-foreground" />
              <input
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder="Search borrowers, IDs, villages…"
                className="bg-transparent outline-none text-sm w-full placeholder:text-muted-foreground"
              />
            </div>
            <AnimatePresence>
              {searchResults.length > 0 && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
                  className="glass absolute right-0 mt-2 w-96 rounded-2xl p-2 overflow-hidden"
                >
                  {searchResults.map((a) => (
                    <button
                      key={a.id}
                      onClick={() => { setQ(""); nav(`/applications/${a.id}`); }}
                      className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-white text-left"
                    >
                      <Avatar name={a.borrower_name} size={32} />
                      <div className="min-w-0 flex-1">
                        <div className="text-sm font-medium truncate">{a.borrower_name}</div>
                        <div className="text-xs text-muted-foreground truncate">{a.id} · {a.village}</div>
                      </div>
                      <span className="text-xs tabular-nums font-medium">{a.score_900}</span>
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Search — mobile icon only */}
          <button className="icon-btn lg:hidden !h-10 !w-10" aria-label="Search"><Search className="h-4 w-4" /></button>

          {/* Quick actions */}
          <div ref={quick.ref} className="relative">
            <button
              onClick={() => quick.setOpen((v) => !v)}
              className="pill !py-1.5 !px-3 gap-1.5"
              aria-label="Quick actions"
            >
              <Plus className="h-4 w-4" />
              <span className="hidden sm:inline">New</span>
              <ChevronDown className="h-3.5 w-3.5 hidden sm:block" />
            </button>
            <AnimatePresence>
              {quick.open && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
                  className="glass absolute right-0 mt-2 w-72 rounded-2xl p-2"
                >
                  {quickActions.map((qa) => (
                    <Link
                      key={qa.to}
                      to={qa.to}
                      onClick={() => quick.setOpen(false)}
                      className="flex items-start gap-3 px-3 py-2.5 rounded-xl hover:bg-white text-left"
                    >
                      <span className="grid place-items-center h-8 w-8 rounded-full bg-primary/10 text-primary shrink-0 mt-0.5">
                        <qa.icon className="h-4 w-4" />
                      </span>
                      <div>
                        <div className="text-sm font-medium">{qa.label}</div>
                        <div className="text-[11px] text-muted-foreground">{qa.sub}</div>
                      </div>
                    </Link>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Notifications */}
          <div ref={notif.ref} className="relative">
            <button
              onClick={() => notif.setOpen((v) => !v)}
              className="icon-btn !h-10 !w-10 relative"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
              <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-rose-500 ring-2 ring-white" />
            </button>
            <AnimatePresence>
              {notif.open && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
                  className="glass absolute right-0 mt-2 w-96 rounded-2xl p-2"
                >
                  <div className="px-3 py-2 flex items-center justify-between">
                    <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Notifications</span>
                    <span className="text-[11px] text-muted-foreground">{formatDateShort(new Date().toISOString())}</span>
                  </div>
                  <ul className="max-h-80 overflow-y-auto">
                    {notifications.map((n) => (
                      <li key={n.id}>
                        <Link
                          to={n.to}
                          onClick={() => notif.setOpen(false)}
                          className="flex items-start gap-3 px-3 py-2.5 rounded-xl hover:bg-white"
                        >
                          <span className={cn(
                            "mt-1.5 h-2 w-2 rounded-full shrink-0",
                            n.tone === "danger" && "bg-rose-500",
                            n.tone === "warning" && "bg-amber-500",
                            n.tone === "success" && "bg-emerald-500",
                          )} />
                          <div className="min-w-0 flex-1">
                            <div className="text-sm font-medium">{n.title}</div>
                            <div className="text-xs text-muted-foreground truncate">{n.detail}</div>
                          </div>
                        </Link>
                      </li>
                    ))}
                  </ul>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Profile */}
          <div ref={profile.ref} className="relative">
            <button
              onClick={() => profile.setOpen((v) => !v)}
              className="rounded-full ring-2 ring-transparent hover:ring-white transition"
              aria-label="Profile"
            >
              <Avatar name={persona.name} size={36} />
            </button>
            <AnimatePresence>
              {profile.open && (
                <motion.div
                  initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: 4 }}
                  className="glass absolute right-0 mt-2 w-64 rounded-2xl p-2"
                >
                  <div className="px-3 py-3 flex items-center gap-3 border-b border-slate-200/40">
                    <Avatar name={persona.name} size={40} />
                    <div className="min-w-0">
                      <div className="text-sm font-semibold truncate">{persona.name}</div>
                      <div className="text-[11px] font-bold text-primary truncate tracking-wide">
                        {persona.role.replace("_", " ")}
                      </div>
                    </div>
                  </div>
                  <div className="px-3 py-2 text-[11px] text-muted-foreground truncate">
                    {persona.id} · {persona.branchOrVillage}
                  </div>
                  <button className="w-full flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-white text-sm">
                    <Settings className="h-4 w-4" /> Settings
                  </button>
                  <button className="w-full flex items-center gap-2 px-3 py-2 rounded-xl hover:bg-white text-sm text-rose-600">
                    <LogOut className="h-4 w-4" /> Sign out (demo)
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* Mobile primary nav strip */}
      <nav className="md:hidden mt-3 flex gap-2 overflow-x-auto no-scrollbar pb-1 max-w-7xl mx-auto">
        {primaryNav.map((n) => (
          <NavLink key={n.to} to={n.to} end={n.end}>
            {({ isActive }) => (
              <span className={cn(
                "inline-flex items-center rounded-full px-3.5 py-1.5 text-xs whitespace-nowrap",
                isActive
                  ? "bg-primary text-primary-foreground shadow-[0_10px_24px_-10px_rgba(31,55,105,0.5)]"
                  : "bg-white/70 text-muted-foreground border border-white/70",
              )}>
                {n.label}
              </span>
            )}
          </NavLink>
        ))}
      </nav>
    </header>
  );
}
