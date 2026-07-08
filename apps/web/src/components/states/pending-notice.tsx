import { Clock } from "lucide-react";

export function PendingNotice({ message }: { message: string }) {
  return (
    <div role="status" className="flex gap-2.5 rounded-lg border border-warning/20 bg-warning/[0.065] p-3 text-sm leading-5 text-warning">
      <Clock className="mt-0.5 size-4 shrink-0" aria-hidden="true" /> {message}
    </div>
  );
}
