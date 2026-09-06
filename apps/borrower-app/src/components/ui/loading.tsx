import { Loader2 } from "lucide-react";

interface LoadingStateProps {
  /** Text shown below the spinner (default: "Loading…") */
  text?: string;
  /** Use "inline" for small sections, "page" for full-page loading */
  size?: "inline" | "page";
}

/**
 * Reusable loading indicator with spinner and optional message.
 */
export function LoadingState({ text = "Loading…", size = "page" }: LoadingStateProps) {
  if (size === "inline") {
    return (
      <div className="flex items-center gap-2 py-4 text-sm text-muted-foreground" role="status">
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>{text}</span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center py-20 gap-3" role="status">
      <Loader2 className="h-8 w-8 animate-spin text-violet-400" />
      <p className="text-sm text-muted-foreground">{text}</p>
    </div>
  );
}
