"use client";

import { FileStack } from "lucide-react";
import { ModulePlaceholder } from "@/components/modules/module-placeholder";
export default function Page(){return <ModulePlaceholder permission="conferences:read" icon={FileStack} title="Documentos" description="Entrada e identificação documental pertencem ao Data Plane." emptyTitle="Documentos ainda não importados" emptyDescription="A importação, classificação e confirmação humana serão habilitadas nas próximas fases. Nenhum arquivo fictício é exibido aqui."/>}
