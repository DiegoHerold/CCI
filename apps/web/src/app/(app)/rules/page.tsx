import { ListChecks } from "lucide-react";
import { ModulePlaceholder } from "@/components/modules/module-placeholder";
export default function Page(){return <ModulePlaceholder permission="conferences:read" icon={ListChecks} title="Regras" description="Regras versionadas que operam exclusivamente sobre variáveis confirmadas." emptyTitle="Regras ainda não configuradas" emptyDescription="A criação e ativação ficarão no Rule Service. Alterações futuras sempre criarão novas versões, sem sobrescrever o histórico."/>}
