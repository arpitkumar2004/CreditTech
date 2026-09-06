import { Inbox, type LucideIcon } from "lucide-react";

interface EmptyStateProps {
  /** Icon component (default: Inbox) */
  icon?: LucideIcon;
  /** Primary message */
  title?: string;
  /** Supporting detail */
  subtitle?: string;
  /** Optional action slot (e.g. a button) */
  children?: React.ReactNode;
}

/**
 * Reusable empty state shown when a list / section has no data.
 */
export function EmptyState({
  icon: Icon = Inbox,
  title = "Nothing here yet",
  subtitle,
  children,
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 gap-3 text-center">
      <div className="w-14 h-14 rounded-full bg-white/5 flex items-center justify-center">
        <Icon className="h-7 w-7 text-muted-foreground" />
      </div>
      <h3 className="font-medium text-sm">{title}</h3>
      {subtitle && <p className="text-xs text-muted-foreground max-w-xs">{subtitle}</p>}
      {children}
    </div>
  );
}
