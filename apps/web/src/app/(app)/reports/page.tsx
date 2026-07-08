import { ScrollText } from "lucide-react";
import { ModulePlaceholder } from "@/components/modules/module-placeholder";
export default function Page(){return <ModulePlaceholder permission="reports:read" icon={ScrollText} title="Relatórios" description="Saídas auditáveis em PDF, Excel e balancete anotado." emptyTitle="Nenhum relatório gerado" emptyDescription="Os artefatos serão produzidos pelo Report Service e por workers a partir de execuções reais. A Web não simula relatórios."/>}
