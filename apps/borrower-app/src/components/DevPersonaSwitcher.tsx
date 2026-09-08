import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Users,
  ShieldAlert,
  ChevronDown,
  Check,
  Building2,
  Wheat,
  Cpu,
} from "lucide-react";
import {
  DEV_PERSONAS,
  getActivePersona,
  setActivePersona,
  type DevPersona,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const ROLE_COLORS: Record<string, { bg: string; text: string; ring: string }> = {
  LOAN_OFFICER: { bg: "bg-blue-500/15", text: "text-blue-700", ring: "ring-blue-400/40" },
  BANK_SAKHI: { bg: "bg-emerald-500/15", text: "text-emerald-700", ring: "ring-emerald-400/40" },
  BORROWER: { bg: "bg-violet-500/15", text: "text-violet-700", ring: "ring-violet-400/40" },
  RISK_OFFICER: { bg: "bg-amber-500/15", text: "text-amber-700", ring: "ring-amber-400/40" },
  ADMIN: { bg: "bg-rose-500/15", text: "text-rose-700", ring: "ring-rose-400/40" },
};

const PERSONA_GROUPS = [
  {
    title: "Borrower Personas (Self-Service & Loan Status)",
    icon: Users,
    keys: ["BORROWER_RADHIKA", "BORROWER_SITA", "BORROWER_RAMU", "BORROWER_MEENA"],
  },
  {
    title: "Bank Sakhi Field Network (Assisted Onboarding)",
    icon: Wheat,
    keys: ["SAKHI_SUNITA", "SAKHI_MANJU"],
  },
  {
    title: "Loan Officers (Branch Underwriting & Overrides)",
    icon: Building2,
    keys: ["OFFICER_RAJESH", "OFFICER_VIKRAM"],
  },
  {
    title: "Governance & Systems (Audits, Parity & MLOps)",
    icon: Cpu,
    keys: ["RISK_PRIYA", "ADMIN_AMIT"],
  },
];

export default function DevPersonaSwitcher() {
  const [active, setActive] = useState<DevPersona>(getActivePersona);
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handlePersonaChange(e: Event) {
      const customEvent = e as CustomEvent<DevPersona>;
      if (customEvent.detail) {
        setActive(customEvent.detail);
      }
    }
    window.addEventListener("credittech_persona_changed", handlePersonaChange);
    return () => {
      window.removeEventListener("credittech_persona_changed", handlePersonaChange);
    };
  }, []);

  useEffect(() => {
    function onDoc(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onEsc(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    if (open) {
      document.addEventListener("mousedown", onDoc);
      document.addEventListener("keydown", onEsc);
    }
    return () => {
      document.removeEventListener("mousedown", onDoc);
      document.removeEventListener("keydown", onEsc);
    };
  }, [open]);

  const selectPersona = (key: string) => {
    setActivePersona(key);
    setActive(DEV_PERSONAS[key]);
    setOpen(false);
    // Trigger lightweight refresh of the page or active route
    window.location.reload();
  };

  const roleTheme = ROLE_COLORS[active.role] ?? {
    bg: "bg-slate-500/15",
    text: "text-slate-700",
    ring: "ring-slate-300",
  };

  return (
    <div ref={ref} className="fixed bottom-4 right-4 z-50 select-none">
      {/* Trigger Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setOpen((prev) => !prev)}
        className={cn(
          "glass flex items-center gap-2.5 px-3.5 py-2 rounded-full shadow-lg border border-white/60",
          "backdrop-blur-md bg-white/80 transition-all cursor-pointer ring-1",
          roleTheme.ring
        )}
        title="Switch active persona for end-to-end testing"
      >
        <span
          className={cn(
            "h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0",
            roleTheme.bg,
            roleTheme.text
          )}
        >
          {active.name.charAt(0)}
        </span>

        <div className="flex flex-col text-left">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-foreground tracking-tight">
              {active.name}
            </span>
            <span
              className={cn(
                "text-[10px] font-bold px-1.5 py-0.2 rounded-full tracking-wider uppercase",
                roleTheme.bg,
                roleTheme.text
              )}
            >
              {active.role.replace("_", " ")}
            </span>
          </div>
          <span className="text-[10px] text-muted-foreground truncate max-w-[150px]">
            {active.id} · {active.branchOrVillage}
          </span>
        </div>

        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 text-muted-foreground transition-transform duration-200 ml-1",
            open && "rotate-180"
          )}
        />
      </motion.button>

      {/* Popover Menu */}
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 10, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ duration: 0.18, ease: "easeOut" }}
            className="glass absolute bottom-14 right-0 w-84 sm:w-96 rounded-2xl p-3 shadow-2xl border border-white/80 backdrop-blur-xl bg-white/90 overflow-hidden"
          >
            <div className="flex items-center justify-between px-2 pb-2.5 border-b border-slate-200/50">
              <div className="flex items-center gap-1.5">
                <Users className="h-4 w-4 text-primary" />
                <span className="text-xs font-bold uppercase tracking-wider text-primary">
                  Dev Persona Switcher
                </span>
              </div>
              <span className="text-[10px] text-muted-foreground bg-slate-100 px-2 py-0.5 rounded-full font-mono">
                Reproducible Test Env
              </span>
            </div>

            <div className="max-h-[380px] overflow-y-auto py-2 space-y-3">
              {PERSONA_GROUPS.map((group) => (
                <div key={group.title} className="space-y-1">
                  <div className="flex items-center gap-1.5 px-2 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">
                    <group.icon className="h-3 w-3" />
                    <span>{group.title}</span>
                  </div>

                  {group.keys.map((k) => {
                    const p = DEV_PERSONAS[k];
                    const isCurrent = p.key === active.key;
                    const pTheme = ROLE_COLORS[p.role] ?? {
                      bg: "bg-slate-100",
                      text: "text-slate-600",
                    };

                    return (
                      <button
                        key={p.key}
                        onClick={() => selectPersona(p.key)}
                        className={cn(
                          "w-full text-left p-2 rounded-xl transition-all flex items-center justify-between group",
                          isCurrent
                            ? "bg-primary/10 border border-primary/20 shadow-sm"
                            : "hover:bg-slate-100/80"
                        )}
                      >
                        <div className="flex items-start gap-2.5 min-w-0">
                          <span
                            className={cn(
                              "h-7 w-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 mt-0.5",
                              pTheme.bg,
                              pTheme.text
                            )}
                          >
                            {p.name.charAt(0)}
                          </span>

                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5">
                              <span
                                className={cn(
                                  "text-xs font-medium truncate",
                                  isCurrent ? "font-bold text-primary" : "text-foreground"
                                )}
                              >
                                {p.name}
                              </span>
                              <span
                                className={cn(
                                  "text-[9px] font-bold px-1 rounded-full uppercase",
                                  pTheme.bg,
                                  pTheme.text
                                )}
                              >
                                {p.role.replace("_", " ")}
                              </span>
                            </div>
                            <div className="text-[10px] text-muted-foreground truncate">
                              {p.description}
                            </div>
                          </div>
                        </div>

                        {isCurrent && (
                          <span className="text-primary ml-2 shrink-0">
                            <Check className="h-4 w-4" />
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              ))}
            </div>

            <div className="pt-2 border-t border-slate-200/50 flex items-center justify-between text-[10px] text-muted-foreground px-2">
              <span className="flex items-center gap-1">
                <ShieldAlert className="h-3 w-3 text-amber-500" />
                RBAC Enforced on Backend
              </span>
              <span className="font-mono text-[9px] text-slate-400">
                Headers: X-Officer / X-Borrower
              </span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
