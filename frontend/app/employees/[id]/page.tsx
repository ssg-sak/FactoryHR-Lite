"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/layout/AppShell";
import { EmptyState, ErrorState, Spinner } from "@/components/ui/Feedback";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import { finiteNumber, formatDate, formatHours, formatNumber, formatTenure } from "@/lib/format";

export default function EmployeeDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const employee = useQuery({
    queryKey: ["employee", id],
    queryFn: () => api.employee(id),
    enabled: Number.isFinite(id),
  });
  const attendance = useQuery({
    queryKey: ["employee-attendance", id],
    queryFn: () => api.attendance({ employee_id: id, page: 1, page_size: 100 }),
    enabled: Number.isFinite(id),
  });

  const records = attendance.data?.items ?? [];
  const overtimeValues = records
    .map((item) => finiteNumber(item.overtime_hours))
    .filter((item): item is number => item !== null);
  const averageOvertime =
    overtimeValues.length > 0
      ? overtimeValues.reduce((sum, value) => sum + value, 0) / overtimeValues.length
      : 0;
  const lateCount = records.filter((item) => item.attendance_status === "late").length;
  const absentCount = records.filter((item) => item.attendance_status === "absent").length;
  const asOf = employee.data?.resigned_at ?? new Date().toISOString().slice(0, 10);

  return (
    <AppShell title="직원 상세" description="직원 기본 정보와 최근 근태">
      <div className="space-y-4">
        <Link href="/employees" className="text-sm text-teal-800 underline">
          목록으로
        </Link>
        {employee.isLoading ? <Spinner /> : null}
        {employee.error instanceof Error ? <ErrorState message={employee.error.message} /> : null}
        {employee.data ? (
          <section className="grid gap-4 md:grid-cols-2">
            <article className="rounded-md border border-slate-200 bg-white p-4">
              <h2 className="text-sm font-semibold text-slate-900">기본정보</h2>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <dt className="text-slate-500">사번</dt>
                <dd>{employee.data.employee_number}</dd>
                <dt className="text-slate-500">이름</dt>
                <dd>{employee.data.name}</dd>
                <dt className="text-slate-500">직책</dt>
                <dd>{employee.data.position ?? "—"}</dd>
                <dt className="text-slate-500">상태</dt>
                <dd>
                  <StatusBadge kind="employee" value={employee.data.status} />
                </dd>
                <dt className="text-slate-500">입사일</dt>
                <dd>{formatDate(employee.data.hired_at)}</dd>
                <dt className="text-slate-500">퇴사일</dt>
                <dd>{formatDate(employee.data.resigned_at)}</dd>
                <dt className="text-slate-500">근속기간</dt>
                <dd>{formatTenure(employee.data.hired_at, employee.data.resigned_at, asOf)}</dd>
              </dl>
            </article>
            <article className="rounded-md border border-slate-200 bg-white p-4">
              <h2 className="text-sm font-semibold text-slate-900">현재 배치</h2>
              <dl className="mt-3 grid grid-cols-2 gap-2 text-sm">
                <dt className="text-slate-500">부서</dt>
                <dd>{employee.data.department_name}</dd>
                <dt className="text-slate-500">공장</dt>
                <dd>{employee.data.factory_name}</dd>
                <dt className="text-slate-500">생산라인</dt>
                <dd>{employee.data.production_line_name ?? "—"}</dd>
                <dt className="text-slate-500">교대조</dt>
                <dd>{employee.data.shift_name}</dd>
                <dt className="text-slate-500">평균 잔업</dt>
                <dd>{formatHours(averageOvertime)} (조회된 근태 기준)</dd>
                <dt className="text-slate-500">지각 / 결근</dt>
                <dd>
                  지각 {formatNumber(lateCount)}건 · 결근 {formatNumber(absentCount)}건
                </dd>
              </dl>
            </article>
          </section>
        ) : null}
        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-slate-900">최근 근태 기록</h2>
          {attendance.isLoading ? <Spinner /> : null}
          {records.length === 0 && !attendance.isLoading ? (
            <div className="mt-3">
              <EmptyState message="선택한 조건에 해당하는 데이터가 없습니다." />
            </div>
          ) : (
            <div className="mt-3 overflow-x-auto">
              <table className="min-w-full text-sm">
                <thead className="bg-slate-50 text-left text-slate-600">
                  <tr>
                    {["날짜", "상태", "근무시간", "잔업시간"].map((header) => (
                      <th key={header} className="px-3 py-2 font-medium">
                        {header}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {records.map((item) => (
                    <tr key={item.id} className="border-t border-slate-200">
                      <td className="px-3 py-2">{formatDate(item.work_date)}</td>
                      <td className="px-3 py-2">
                        <StatusBadge kind="attendance" value={item.attendance_status} />
                      </td>
                      <td className="px-3 py-2">{formatHours(item.work_hours)}</td>
                      <td className="px-3 py-2">{formatHours(item.overtime_hours)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>
    </AppShell>
  );
}
