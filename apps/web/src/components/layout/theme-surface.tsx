import { cn } from "@/lib/utils";

export function ThemeSurface({ className, ...props }: React.ComponentProps<"section">) {
  return <section className={cn("glass-panel rounded-xl", className)} {...props} />;
}
