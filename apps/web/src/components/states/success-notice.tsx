import { CheckCircle2 } from "lucide-react";

export function SuccessNotice({ message }: { message: string }) {
  return (
    <div role="status" className="flex gap-2.5 rounded-lg border border-success/20 bg-success/[0.065] p-3 text-sm leading-5 text-success">
      <CheckCircle2 className="mt-0.5 size-4 shrink-0" aria-hidden="true" /> {message}
    </div>
  );
}
