import { BookOpenCheck } from "lucide-react";
import { ModulePlaceholder } from "@/components/modules/module-placeholder";
export default function Page(){return <ModulePlaceholder permission="conferences:read" icon={BookOpenCheck} title="Auditoria" description="Explicação de negócio das regras, valores, documentos e evidências usados." emptyTitle="Auditoria ainda não produzida" emptyDescription="A trilha contábil aparecerá após execuções reais. Logs técnicos permanecem separados da explicação de negócio."/>}
