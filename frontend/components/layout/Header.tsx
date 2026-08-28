"use client";

import { useAuth } from "@/components/auth/AuthContext";

export function Header({ title, description }: { title: string; description: string }) {
  const { user, logout } = useAuth();
  const roleLabel = user?.role === "admin" ? "admin" : "viewer";
  return (
    <header className="border-b border-slate-200 bg-white px-6 py-3">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-lg font-semibold text-slate-900">{title}</h1>
          <p className="mt-0.5 text-sm text-slate-500">{description}</p>
        </div>
        {user ? (
          <div className="flex items-center gap-3 text-sm">
            <span className="text-slate-600">
              {user.username}
              <span className="ml-2 rounded bg-slate-100 px-1.5 py-0.5 text-xs text-slate-700">
                {roleLabel}
              </span>
            </span>
            <button
              type="button"
              className="rounded border border-slate-300 bg-white px-2.5 py-1.5 text-slate-700"
              onClick={logout}
            >
              로그아웃
            </button>
          </div>
        ) : null}
      </div>
    </header>
  );
}
