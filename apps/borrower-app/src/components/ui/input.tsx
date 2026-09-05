import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => (
    <input
      type={type}
      ref={ref}
      className={cn(
        "flex h-11 w-full rounded-xl border border-white/70 bg-white/70 backdrop-blur px-4 py-2 text-sm",
        "shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_1px_2px_rgba(31,55,105,0.06)]",
        "placeholder:text-muted-foreground/70 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/40",
        "disabled:cursor-not-allowed disabled:opacity-50 transition-shadow",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";
