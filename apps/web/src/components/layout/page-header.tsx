import { Badge } from "@/components/ui/badge";

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  action?: React.ReactNode;
}) {
  return (
    <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-3xl">
        {eyebrow && <Badge variant="info" className="mb-3 uppercase">{eyebrow}</Badge>}
        <h1 className="text-2xl font-semibold tracking-[-0.035em] text-white sm:text-[2rem]">{title}</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted sm:text-[0.94rem]">{description}</p>
      </div>
      {action}
    </header>
  );
}
