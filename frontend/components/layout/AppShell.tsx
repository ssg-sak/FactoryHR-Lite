import type { ReactNode } from "react";
import { AuthGate } from "@/components/auth/AuthGate";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";

export function AppShell({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <AuthGate>
      <div className="flex min-h-screen bg-slate-100">
        <Sidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header title={title} description={description} />
          <main className="flex-1 p-6">{children}</main>
        </div>
      </div>
    </AuthGate>
  );
}
