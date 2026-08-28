"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/auth/AuthContext";
import { ApiError } from "@/lib/errors";
import { DEMO_VIEWER_PASSWORD, DEMO_VIEWER_USERNAME } from "@/lib/auth";

export default function LoginPage() {
  const { login, isAuthenticated, isReady } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (isReady && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isReady, router]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(username, password);
      router.replace("/dashboard");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "로그인에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-100 px-4 py-8">
      <section className="w-full max-w-md rounded-md border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold tracking-wide text-slate-900">FactoryHR Lite</p>
        <p className="mt-1 text-[13px] text-slate-500">Manufacturing Workforce Operations</p>
        <h1 className="mt-4 text-lg font-semibold text-slate-900">로그인</h1>
        <p className="mt-1 text-sm text-slate-500">
          사내 직원·근태 운영 시스템 데모입니다. 공개 회원가입을 제공하지 않습니다.
        </p>
        <form className="mt-5 space-y-3" onSubmit={onSubmit}>
          <label className="block text-xs font-medium text-slate-600">
            사용자 이름
            <input
              className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
              name="username"
              autoComplete="username"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              required
            />
          </label>
          <label className="block text-xs font-medium text-slate-600">
            비밀번호
            <input
              className="mt-1 block w-full rounded border border-slate-300 px-3 py-2 text-sm"
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          {error ? <p className="text-sm text-rose-700">{error}</p> : null}
          <button
            type="submit"
            className="w-full rounded bg-teal-800 px-3 py-2 text-sm font-medium text-white disabled:opacity-50"
            disabled={submitting}
          >
            {submitting ? "로그인 중..." : "로그인"}
          </button>
        </form>
        <aside className="mt-5 rounded border border-slate-200 bg-slate-50 p-3 text-xs leading-5 text-slate-600">
          <p className="font-medium text-slate-800">DEMO ACCOUNT (조회 전용)</p>
          <p className="mt-1">
            사용자 이름 <span className="font-mono">{DEMO_VIEWER_USERNAME}</span> / 비밀번호{" "}
            <span className="font-mono">{DEMO_VIEWER_PASSWORD}</span>
          </p>
          <p className="mt-1">데이터는 합성된 데모 직원·근태입니다. viewer는 조회만 가능합니다.</p>
        </aside>
      </section>
    </main>
  );
}
