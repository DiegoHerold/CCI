"use client";

import { Activity } from "lucide-react";
import { ModulePlaceholder } from "@/components/modules/module-placeholder";
export default function Page(){return <ModulePlaceholder permission="conferences:read" icon={Activity} title="Execuções" description="Orquestração das conferências por cliente e competência." emptyTitle="Nenhuma execução disponível" emptyDescription="Workflows longos, retentativas e reprocessamentos serão conduzidos pelo Execution Control Service, Temporal e workers — nunca por uma request da Web."/>}
