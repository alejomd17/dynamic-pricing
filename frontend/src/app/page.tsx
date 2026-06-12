"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-white">
      <div className="text-center">
        <div
          className="animate-spin rounded-full h-14 w-14 border-b-2 mx-auto mb-5"
          style={{ borderColor: "#00285d" }}
        />
        <p className="text-slate-400 text-sm">Cargando aplicación...</p>
      </div>
    </div>
  );
}
