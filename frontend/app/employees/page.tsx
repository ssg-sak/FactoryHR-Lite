"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { EmployeeForm } from "@/components/employees/EmployeeForm";
import { FilterBar } from "@/components/filters/FilterBar";
import { useAuth } from "@/components/auth/AuthContext";
import { AppShell } from "@/components/layout/AppShell";
import { EmptyState, ErrorState, Spinner } from "@/components/ui/Feedback";
import { Modal } from "@/components/ui/Modal";
import { Pagination } from "@/components/ui/Pagination";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { ApiError } from "@/lib/errors";
import type { Employee, EmployeeWritePayload, WorkforceFilters } from "@/lib/types";

export default function EmployeesPage() {
  const { canWrite } = useAuth();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState<WorkforceFilters>({});
  const [name, setName] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [editor, setEditor] = useState<"create" | Employee | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  const list = useQuery({
    queryKey: ["employees", filters, name, status, page],
    queryFn: () =>
      api.employees({
        page,
        page_size: 20,
        name: name || undefined,
        status: status || undefined,
        department_id: filters.department_id,
        factory_id: filters.factory_id,
        production_line_id: filters.production_line_id,
        shift_id: filters.shift_id,
      }),
  });

  const createMutation = useMutation({
    mutationFn: api.createEmployee,
    onSuccess: async () => {
      setEditor(null);
      await queryClient.invalidateQueries({ queryKey: ["employees"] });
    },
    onError: (error: unknown) => {
      setFormError(error instanceof ApiError ? error.message : "저장에 실패했습니다.");
    },
  });
  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<EmployeeWritePayload> }) =>
      api.updateEmployee(id, payload),
    onSuccess: async () => {
      setEditor(null);
      await queryClient.invalidateQueries({ queryKey: ["employees"] });
    },
    onError: (error: unknown) => {
      setFormError(error instanceof ApiError ? error.message : "저장에 실패했습니다.");
    },
  });
  const deleteMutation = useMutation({
    mutationFn: api.deleteEmployee,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["employees"] });
    },
  });

  return (
    <AppShell title="직원 관리" description="직원 검색, 필터, 등록/수정/삭제">
      <div className="space-y-4">
        <FilterBar
          value={filters}
          showDates={false}
          onChange={(next) => {
            setPage(1);
            setFilters({ ...next, date_from: undefined, date_to: undefined });
          }}
          onReset={() => {
            setFilters({});
            setName("");
            setStatus("");
            setPage(1);
          }}
        />
        <div className="flex flex-wrap items-end gap-3">
          <label className="text-xs font-medium text-slate-600">
            이름 검색
            <input
              className="mt-1 block rounded border border-slate-300 px-3 py-2 text-sm"
              value={name}
              onChange={(event) => {
                setPage(1);
                setName(event.target.value);
              }}
            />
          </label>
          <label className="text-xs font-medium text-slate-600">
            상태
            <select
              className="mt-1 block rounded border border-slate-300 px-3 py-2 text-sm"
              value={status}
              onChange={(event) => {
                setPage(1);
                setStatus(event.target.value);
              }}
            >
              <option value="">전체</option>
              <option value="active">재직</option>
              <option value="resigned">퇴사</option>
            </select>
          </label>
          {canWrite ? (
            <button
              type="button"
              className="rounded bg-teal-800 px-3 py-2 text-sm text-white"
              onClick={() => {
                setFormError(null);
                setEditor("create");
              }}
            >
              직원 등록
            </button>
          ) : null}
        </div>
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
                  {["사번", "이름", "부서", "공장", "생산라인", "교대조", "직책", "입사일", "상태", "작업"].map(
                    (header) => (
                      <th key={header} className="px-3 py-2 font-medium">
                        {header}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                {list.data.items.map((employee) => (
                  <tr key={employee.id} className="border-t border-slate-200">
                    <td className="px-3 py-2">{employee.employee_number}</td>
                    <td className="px-3 py-2">{employee.name}</td>
                    <td className="px-3 py-2">{employee.department_name}</td>
                    <td className="px-3 py-2">{employee.factory_name}</td>
                    <td className="px-3 py-2">{employee.production_line_name ?? "—"}</td>
                    <td className="px-3 py-2">{employee.shift_name}</td>
                    <td className="px-3 py-2">{employee.position ?? "—"}</td>
                    <td className="px-3 py-2">{formatDate(employee.hired_at)}</td>
                    <td className="px-3 py-2">
                      <StatusBadge kind="employee" value={employee.status} />
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex gap-2">
                        <Link className="text-teal-800 underline" href={`/employees/${employee.id}`}>
                          상세
                        </Link>
                        {canWrite ? (
                          <>
                            <button
                              type="button"
                              className="text-slate-700 underline"
                              onClick={() => {
                                setFormError(null);
                                setEditor(employee);
                              }}
                            >
                              수정
                            </button>
                            <button
                              type="button"
                              className="text-rose-700 underline"
                              onClick={() => {
                                if (window.confirm(`${employee.name} 직원을 삭제할까요?`)) {
                                  deleteMutation.mutate(employee.id);
                                }
                              }}
                            >
                              삭제
                            </button>
                          </>
                        ) : null}
                      </div>
                      {deleteMutation.error instanceof Error &&
                      deleteMutation.variables === employee.id ? (
                        <p className="mt-1 text-xs text-rose-700">{deleteMutation.error.message}</p>
                      ) : null}
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
        <Modal
          title={editor === "create" ? "직원 등록" : "직원 수정"}
          onClose={() => setEditor(null)}
        >
          <EmployeeForm
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
