import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.98]",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-[0_10px_24px_-8px_rgba(31,55,105,0.55)] hover:brightness-110",
        destructive:
          "bg-destructive text-destructive-foreground shadow-[0_10px_24px_-10px_rgba(200,50,50,0.55)] hover:brightness-110",
        outline:
          "border border-white/60 bg-white/70 backdrop-blur hover:bg-white shadow-[0_6px_16px_-8px_rgba(31,55,105,0.25)]",
        secondary:
          "bg-secondary/80 text-secondary-foreground hover:bg-secondary",
        ghost: "hover:bg-white/60",
        link: "text-primary underline-offset-4 hover:underline",
      },
      size: {
        default: "h-11 px-5 rounded-full text-sm",
        sm: "h-9 px-4 rounded-full text-sm",
        lg: "h-12 px-7 rounded-full text-base",
        icon: "h-11 w-11 rounded-full",
      },
    },
    defaultVariants: { variant: "default", size: "default" },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp className={cn(buttonVariants({ variant, size, className }))} ref={ref} {...props} />;
  }
);
Button.displayName = "Button";

export { buttonVariants };
