import {
  Activity,
  BookOpenCheck,
  Boxes,
  Building2,
  CalendarRange,
  FileStack,
  Gauge,
  ListChecks,
  ScrollText,
  ScanLine,
  Settings2,
  SlidersHorizontal,
  Users,
} from "lucide-react";

export const navigationGroups = [
  {
    label: "Operação",
    items: [
      { label: "Dashboard", href: "/dashboard", icon: Gauge },
      { label: "Clientes", href: "/clients", icon: Building2, permission: "clients:read" },
      { label: "Competências", href: "/competencies", icon: CalendarRange, permission: "client-competencies:read" },
      { label: "Documentos", href: "/documents", icon: FileStack, permission: "conferences:read" },
      { label: "Execuções", href: "/executions", icon: Activity, permission: "conferences:read", future: true },
    ],
  },
  {
    label: "Configuração",
    items: [
      { label: "Modelos", href: "/models", icon: Boxes, permission: "conferences:read", future: true },
      { label: "Templates", href: "/templates", icon: ScanLine, permission: "conferences:read" },
      { label: "Variáveis", href: "/variables", icon: SlidersHorizontal, permission: "conferences:read", future: true },
      { label: "Regras", href: "/rules", icon: ListChecks, permission: "conferences:read", future: true },
    ],
  },
  {
    label: "Administração",
    items: [
      { label: "Usuários", href: "/users", icon: Users, permission: "users:read" },
    ],
  },
  {
    label: "Governança",
    items: [
      { label: "Auditoria", href: "/audit", icon: BookOpenCheck, permission: "conferences:read", future: true },
      { label: "Relatórios", href: "/reports", icon: ScrollText, permission: "reports:read", future: true },
      { label: "Configurações", href: "/settings", icon: Settings2 },
      { label: "Status dos serviços", href: "/settings/services", icon: Activity },
    ],
  },
] as const;
