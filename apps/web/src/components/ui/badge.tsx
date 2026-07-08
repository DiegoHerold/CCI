import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[0.68rem] font-semibold tracking-[0.04em]",
  {
    variants: {
      variant: {
        neutral: "border-white/10 bg-white/[0.045] text-muted-strong",
        info: "border-primary/20 bg-primary/8 text-primary",
        success: "border-success/20 bg-success/8 text-success",
        warning: "border-warning/20 bg-warning/8 text-warning",
        danger: "border-danger/20 bg-danger/8 text-danger",
        violet: "border-violet/20 bg-violet/8 text-violet",
      },
    },
    defaultVariants: { variant: "neutral" },
  },
);

export function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<"span"> & VariantProps<typeof badgeVariants>) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />;
}
