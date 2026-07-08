"use client";

import { Boxes } from "lucide-react";
import { ModulePlaceholder } from "@/components/modules/module-placeholder";
export default function Page(){return <ModulePlaceholder permission="conferences:read" icon={Boxes} title="Modelos de conferência" description="Configuração reutilizável por cliente, respeitando versões e documentos esperados." emptyTitle="Modelos ainda não configurados" emptyDescription="O Conference Model Service definirá documentos esperados, grupos e configurações sem misturar responsabilidades com a Web."/>}
