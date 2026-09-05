import { cn } from "@/lib/utils";

const tones = {
  neutral: "bg-white/70 text-muted-foreground border-white",
  success: "bg-emerald-50 text-emerald-700 border-emerald-100",
  warning: "bg-amber-50 text-amber-700 border-amber-100",
  danger:  "bg-rose-50 text-rose-700 border-rose-100",
  info:    "bg-sky-50 text-sky-700 border-sky-100",
  primary: "bg-primary/10 text-primary border-primary/10",
} as const;

export function Badge({
  tone = "neutral",
  children,
  className,
}: {
  tone?: keyof typeof tones;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}

export function Dot({ tone = "neutral" }: { tone?: "success" | "warning" | "danger" | "info" | "neutral" }) {
  const c = {
    success: "bg-emerald-500",
    warning: "bg-amber-500",
    danger: "bg-rose-500",
    info: "bg-sky-500",
    neutral: "bg-slate-400",
  }[tone];
  return <span className={cn("h-1.5 w-1.5 rounded-full", c)} />;
}
