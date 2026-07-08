import * as React from "react";
import { cn } from "@/lib/utils";

export function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      className={cn(
        "h-11 w-full rounded-lg border border-border-strong bg-black/20 px-3.5 text-sm text-foreground shadow-inner shadow-black/10 transition placeholder:text-muted/65 hover:border-white/25 focus:border-primary/70 focus:ring-3 focus:ring-primary/10 disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      {...props}
    />
  );
}
