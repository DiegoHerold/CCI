import { cn } from "@/lib/utils";

export function Skeleton({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-[linear-gradient(90deg,rgba(255,255,255,.035),rgba(255,255,255,.075),rgba(255,255,255,.035))] bg-[length:200%_100%]",
        className,
      )}
      {...props}
    />
  );
}
