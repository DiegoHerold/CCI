"use client";
import { ErrorState } from "@/components/states/error-state";
export default function GlobalError({reset}:{error:Error&{digest?:string};reset:()=>void}){return <div className="min-h-screen p-6"><ErrorState title="A Web encontrou um erro inesperado" description="Nenhum detalhe técnico foi exibido. Tente reconstruir esta tela." onRetry={reset}/></div>}
