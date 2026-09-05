import { cn, initials } from "@/lib/utils";

export function Avatar({ name, size = 40, className }: { name: string; size?: number; className?: string }) {
  const bg = "bg-gradient-to-br from-primary/90 to-primary";
  return (
    <span
      className={cn(
        "inline-grid place-items-center rounded-full text-primary-foreground font-semibold text-xs shadow-inner border border-white/40",
        bg,
        className,
      )}
      style={{ width: size, height: size }}
    >
      {initials(name)}
    </span>
  );
}
