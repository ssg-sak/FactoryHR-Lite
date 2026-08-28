"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { AttendanceForm } from "@/components/attendance/AttendanceForm";
import { AppShell } from "@/components/layout/AppShell";
import { EmptyState, ErrorState, Spinner } from "@/components/ui/Feedback";
import { Modal } from "@/components/ui/Modal";
import { Pagination } from "@/components/ui/Pagination";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import { DEFAULT_DATE_FROM, DEFAULT_DATE_TO } from "@/lib/constants";
import { ApiError } from "@/lib/errors";
import { formatDate, formatHours } from "@/lib/format";
import type { Attendance, AttendanceWritePayload } from "@/lib/types";

export default function AttendancePage() {
  const queryClient = useQueryClient();
  const [dateFrom, setDateFrom] = useState(DEFAULT_DATE_FROM);
  const [dateTo, setDateTo] = useState(DEFAULT_DATE_TO);
  const [employeeId, setEmployeeId] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [editor, setEditor] = useState<"create" | Attendance | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const employees = useQuery({
    queryKey: ["employees-options"],
    queryFn: () => api.employees({ page: 1, page_size: 100 }),
  });
  const list = useQuery({
    queryKey: ["attendance", dateFrom, dateTo, employeeId, status, page],
    queryFn: () =>
      api.attendance({
        page,
        page_size: 20,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        employee_id: employeeId ? Number(employeeId) : undefined,
        attendance_status: status || undefined,
      }),
  });

  const createMutation = useMutation({
    mutationFn: api.createAttendance,
    onSuccess: async () => {
      setEditor(null);
      await queryClient.invalidateQueries({ queryKey: ["attendance"] });
    },
    onError: (error: unknown) => {
      setFormError(error instanceof ApiError ? error.message : "저장에 실패했습니다.");
    },
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<AttendanceWritePayload> }) =>
      api.updateAttendance(id, payload),
    onSuccess: async () => {
      setEditor(null);
      await queryClient.invalidateQueries({ queryKey: ["attendance"] });
    },
    onError: (error: unknown) => {
      setFormError(error instanceof ApiError ? error.message : "저장에 실패했습니다.");
    },
  });
  const deleteMutation = useMutation({
    mutationFn: api.deleteAttendance,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["attendance"] });
    },
  });

  return (
    <AppShell title="근태 관리" description="근태 조회와 등록. 입사 전·퇴사 후 날짜에는 근태를 등록할 수 없습니다.">
      <div className="space-y-4">
        <section className="grid gap-3 rounded-md border border-slate-200 bg-white p-4 md:grid-cols-5">
          <label className="text-xs font-medium text-slate-600">
            시작일
            <input
              type="date"
              className="mt-1 block w-full rounded border border-slate-300 px-2 py-2 text-sm"
              value={dateFrom}
              onChange={(event) => {
                setPage(1);
                setDateFrom(event.target.value);
              }}
            />
          </label>
          <label className="text-xs font-medium text-slate-600">
            종료일
            <input
              type="date"
              className="mt-1 block w-full rounded border border-slate-300 px-2 py-2 text-sm"
              value={dateTo}
              onChange={(event) => {
                setPage(1);
                setDateTo(event.target.value);
              }}
            />
          </label>
          <label className="text-xs font-medium text-slate-600">
            직원
            <select
              className="mt-1 block w-full rounded border border-slate-300 px-2 py-2 text-sm"
              value={employeeId}
              onChange={(event) => {
                setPage(1);
                setEmployeeId(event.target.value);
              }}
            >
              <option value="">전체</option>
              {employees.data?.items.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.employee_number} {item.name}
                </option>
              ))}
            </select>
          </label>
          <label className="text-xs font-medium text-slate-600">
            근태 상태
            <select
              className="mt-1 block w-full rounded border border-slate-300 px-2 py-2 text-sm"
              value={status}
              onChange={(event) => {
                setPage(1);
                setStatus(event.target.value);
              }}
            >
              <option value="">전체</option>
              <option value="present">정상</option>
              <option value="late">지각</option>
              <option value="absent">결근</option>
              <option value="leave">휴가</option>
            </select>
          </label>
          <div className="flex items-end">
            <button
              type="button"
              className="rounded bg-teal-800 px-3 py-2 text-sm text-white"
              onClick={() => {
                setFormError(null);
                setEditor("create");
              }}
            >
              근태 등록
            </button>
          </div>
        </section>
        {list.isLoading ? <Spinner /> : null}
        {list.error instanceof Error ? <ErrorState message={list.error.message} /> : null}
        {list.data && list.data.items.length === 0 ? (
          <EmptyState message="선택한 조건에 해당하는 데이터가 없습니다." />
        ) : null}
        {list.data && list.data.items.length > 0 ? (
          <div className="overflow-x-auto rounded-md border border-slate-200 bg-white">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-50 text-left text-slate-600">
                <tr>
                  {[
                    "날짜",
                    "사번",
                    "직원명",
                    "공장",
                    "생산라인",
                    "교대조",
                    "상태",
                    "근무시간",
                    "잔업시간",
                    "작업",
                  ].map((header) => (
                    <th key={header} className="px-3 py-2 font-medium">
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {list.data.items.map((item) => (
                  <tr key={item.id} className="border-t border-slate-200">
                    <td className="px-3 py-2">{formatDate(item.work_date)}</td>
                    <td className="px-3 py-2">{item.employee_number}</td>
                    <td className="px-3 py-2">{item.employee_name}</td>
                    <td className="px-3 py-2">{item.factory_name}</td>
                    <td className="px-3 py-2">{item.production_line_name ?? "—"}</td>
                    <td className="px-3 py-2">{item.shift_name}</td>
                    <td className="px-3 py-2">
                      <StatusBadge kind="attendance" value={item.attendance_status} />
                    </td>
                    <td className="px-3 py-2">{formatHours(item.work_hours)}</td>
                    <td className="px-3 py-2">{formatHours(item.overtime_hours)}</td>
                    <td className="px-3 py-2">
                      <div className="flex gap-2">
                        <button
                          type="button"
                          className="text-slate-700 underline"
                          onClick={() => {
                            setFormError(null);
                            setEditor(item);
                          }}
                        >
                          수정
                        </button>
                        <button
                          type="button"
                          className="text-rose-700 underline"
                          onClick={() => {
                            if (window.confirm("이 근태 기록을 삭제할까요?")) {
                              deleteMutation.mutate(item.id);
                            }
                          }}
                        >
                          삭제
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        {list.data ? (
          <Pagination
            page={list.data.page}
            pageSize={list.data.page_size}
            total={list.data.total}
            onPageChange={setPage}
          />
        ) : null}
      </div>
      {editor ? (
        <Modal title={editor === "create" ? "근태 등록" : "근태 수정"} onClose={() => setEditor(null)}>
          <AttendanceForm
            initial={editor === "create" ? undefined : editor}
            submitting={createMutation.isPending || updateMutation.isPending}
            error={formError}
            onCancel={() => setEditor(null)}
            onSubmit={(payload) => {
              setFormError(null);
              if (editor === "create") {
                createMutation.mutate(payload);
              } else {
                updateMutation.mutate({ id: editor.id, payload });
              }
            }}
          />
        </Modal>
      ) : null}
    </AppShell>
  );
}
