import { AlertCircle } from "lucide-react";

export function FormErrorState({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div role="alert" className="flex gap-2.5 rounded-lg border border-danger/20 bg-danger/[0.065] p-3 text-sm leading-5 text-danger">
      <AlertCircle className="mt-0.5 size-4 shrink-0" aria-hidden="true" /> {message}
    </div>
  );
}
