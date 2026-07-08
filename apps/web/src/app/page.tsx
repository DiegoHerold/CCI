"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { LoadingState } from "@/components/states/loading-state";
import { useAuth } from "@/features/auth/auth-provider";

export default function HomePage() {
  const { status } = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (status === "authenticated") router.replace("/dashboard");
    if (status === "unauthenticated") router.replace("/login");
  }, [router, status]);
  return <LoadingState fullScreen />;
}
