/**
 * O pacote lucide-react instalado neste ambiente não inclui
 * `dist/lucide-react.d.ts` (instalação incompleta de node_modules,
 * pré-existente e fora do escopo desta fase). Esta declaração ambiente
 * mínima permite que `tsc --noEmit` funcione sem alterar o runtime: o
 * bundler (Next/webpack) continua resolvendo o JavaScript real do pacote
 * normalmente. Remover este arquivo assim que a instalação for corrigida
 * (`npm install` limpo) e os tipos oficiais voltarem a ser encontrados.
 */
declare module "lucide-react" {
  import type { ComponentType, SVGProps } from "react";

  export type LucideIcon = ComponentType<SVGProps<SVGSVGElement> & { size?: number | string }>;

  const icon: LucideIcon;
  export default icon;

  export const Activity: LucideIcon;
  export const AlertCircle: LucideIcon;
  export const AlertTriangle: LucideIcon;
  export const ArrowRight: LucideIcon;
  export const ArrowUpRight: LucideIcon;
  export const Binary: LucideIcon;
  export const BookOpenCheck: LucideIcon;
  export const Boxes: LucideIcon;
  export const Building2: LucideIcon;
  export const CalendarDays: LucideIcon;
  export const CalendarRange: LucideIcon;
  export const CheckCircle2: LucideIcon;
  export const ChevronDown: LucideIcon;
  export const Clock: LucideIcon;
  export const Clock3: LucideIcon;
  export const CircleDashed: LucideIcon;
  export const FileCheck2: LucideIcon;
  export const FileSearch: LucideIcon;
  export const FileStack: LucideIcon;
  export const Fingerprint: LucideIcon;
  export const FolderClock: LucideIcon;
  export const Gauge: LucideIcon;
  export const GitCompareArrows: LucideIcon;
  export const Inbox: LucideIcon;
  export const KeyRound: LucideIcon;
  export const ListChecks: LucideIcon;
  export const LoaderCircle: LucideIcon;
  export const LockKeyhole: LucideIcon;
  export const LogOut: LucideIcon;
  export const Mail: LucideIcon;
  export const MapPin: LucideIcon;
  export const Menu: LucideIcon;
  export const PlugZap: LucideIcon;
  export const Plus: LucideIcon;
  export const Radio: LucideIcon;
  export const RotateCcw: LucideIcon;
  export const ScanLine: LucideIcon;
  export const ScrollText: LucideIcon;
  export const Search: LucideIcon;
  export const Settings2: LucideIcon;
  export const ShieldAlert: LucideIcon;
  export const ShieldCheck: LucideIcon;
  export const ShieldX: LucideIcon;
  export const SlidersHorizontal: LucideIcon;
  export const UserRound: LucideIcon;
  export const UserRoundX: LucideIcon;
  export const Users: LucideIcon;
  export const Variable: LucideIcon;
  export const Workflow: LucideIcon;
  export const X: LucideIcon;
}
