import { Link } from "react-router-dom";
import { ShieldAlert, ArrowLeft, Users } from "lucide-react";
import { motion } from "framer-motion";
import { usePersona } from "@/lib/usePersona";
import { setActivePersona, DEV_PERSONAS } from "@/lib/api";

interface AccessDeniedProps {
  resourceName: string;
  allowedRoles: string[];
}

export default function AccessDenied({ resourceName, allowedRoles }: AccessDeniedProps) {
  const persona = usePersona();

  // Find a persona that has access to suggest to the developer/tester
  const suggestedPersonaKey = Object.keys(DEV_PERSONAS).find((key) =>
    allowedRoles.includes(DEV_PERSONAS[key].role) || DEV_PERSONAS[key].role === "ADMIN"
  ) ?? "OFFICER_RAJESH";
  const suggestedPersona = DEV_PERSONAS[suggestedPersonaKey];

  const handleQuickSwitch = () => {
    setActivePersona(suggestedPersonaKey);
    window.location.reload();
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="max-w-2xl mx-auto my-12 p-8 glass rounded-3xl border border-rose-500/20 shadow-xl text-center space-y-6"
    >
      <div className="inline-grid place-items-center h-16 w-16 rounded-3xl bg-rose-500/10 text-rose-600 mx-auto shadow-inner ring-1 ring-rose-500/30">
        <ShieldAlert className="h-8 w-8" />
      </div>

      <div className="space-y-2">
        <span className="text-[11px] font-mono uppercase tracking-widest px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-700 font-bold">
          HTTP 403 Forbidden · RBAC Violation
        </span>
        <h2 className="text-2xl font-bold tracking-tight text-foreground">
          Access Restricted: {resourceName}
        </h2>
        <p className="text-sm text-muted-foreground max-w-md mx-auto">
          Your current persona does not hold the permissions required to view or mutate this resource.
        </p>
      </div>

      {/* Role details table */}
      <div className="glass-soft rounded-2xl p-4 text-left space-y-3 text-xs">
        <div className="flex items-center justify-between border-b border-slate-200/50 pb-2">
          <span className="text-muted-foreground">Current Active Persona:</span>
          <span className="font-semibold text-foreground flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-rose-500" />
            {persona.name} ({persona.role})
          </span>
        </div>
        <div className="flex items-center justify-between border-b border-slate-200/50 pb-2">
          <span className="text-muted-foreground">Required Role(s):</span>
          <span className="font-mono font-medium text-primary">
            {allowedRoles.join("  |  ")}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-muted-foreground">Enforcement Level:</span>
          <span className="text-emerald-700 font-medium">
            Active on Backend FastAPI Router
          </span>
        </div>
      </div>

      {/* Quick resolution for testing */}
      <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
        <button
          onClick={handleQuickSwitch}
          className="pill gap-2 text-xs w-full sm:w-auto"
        >
          <Users className="h-3.5 w-3.5" />
          Switch to {suggestedPersona.name} ({suggestedPersona.role.replace("_", " ")})
        </button>

        <Link to="/" className="pill-ghost gap-1.5 text-xs w-full sm:w-auto">
          <ArrowLeft className="h-3.5 w-3.5" />
          Return to My Portal
        </Link>
      </div>
    </motion.div>
  );
}
