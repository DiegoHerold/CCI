import { SlidersHorizontal } from "lucide-react";
import { ModulePlaceholder } from "@/components/modules/module-placeholder";
export default function Page(){return <ModulePlaceholder permission="conferences:read" icon={SlidersHorizontal} title="Variáveis" description="Catálogo de dados normalizados e confirmados, com origem, confiança e evidência." emptyTitle="Variáveis ainda não disponíveis" emptyDescription="As regras consumirão apenas variáveis confirmadas pelo Variable Registry Service. A Web nunca lerá arquivos brutos para avaliá-las."/>}
