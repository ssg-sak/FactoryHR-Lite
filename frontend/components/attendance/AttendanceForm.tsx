"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { api } from "@/lib/api";
import type { Attendance, AttendanceWritePayload } from "@/lib/types";

const schema = z.object({
  employee_id: z.coerce.number().int().positive("직원을 선택하세요."),
  work_date: z.string().min(1, "날짜를 입력하세요."),
  work_hours: z.coerce.number().min(0, "근무시간은 0 이상이어야 합니다.").max(16, "근무시간은 16시간을 넘을 수 없습니다."),
  overtime_hours: z.coerce
    .number()
    .min(0, "잔업시간은 0 이상이어야 합니다.")
    .max(8, "잔업시간은 8시간을 넘을 수 없습니다."),
  attendance_status: z.enum(["present", "late", "absent", "leave"]),
});

type FormValues = z.infer<typeof schema>;
const fieldClass =
  "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-900";

export function AttendanceForm({
  initial,
  submitting,
  error,
  onSubmit,
  onCancel,
}: {
  initial?: Attendance;
  submitting: boolean;
  error: string | null;
  onSubmit: (payload: AttendanceWritePayload) => void;
  onCancel: () => void;
}) {
  const employees = useQuery({
    queryKey: ["employees-options"],
    queryFn: () => api.employees({ page: 1, page_size: 100 }),
  });
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      employee_id: initial?.employee_id ?? 0,
      work_date: initial?.work_date ?? "",
      work_hours: Number(initial?.work_hours ?? 8),
      overtime_hours: Number(initial?.overtime_hours ?? 0),
      attendance_status: initial?.attendance_status ?? "present",
    },
  });

  return (
    <form className="grid gap-3" onSubmit={form.handleSubmit((values) => onSubmit(values))}>
      {error ? (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
          {error}
        </p>
      ) : null}
      <label className="text-xs font-medium text-slate-600">
        직원
        <select className={fieldClass} {...form.register("employee_id")}>
          <option value="">선택</option>
          {employees.data?.items.map((item) => (
            <option key={item.id} value={item.id}>
              {item.employee_number} {item.name}
            </option>
          ))}
        </select>
        <span className="mt-1 block text-xs text-red-700">
          {form.formState.errors.employee_id?.message}
        </span>
      </label>
      <label className="text-xs font-medium text-slate-600">
        날짜
        <input type="date" className={fieldClass} {...form.register("work_date")} />
        <span className="mt-1 block text-xs text-red-700">
          {form.formState.errors.work_date?.message}
        </span>
      </label>
      <label className="text-xs font-medium text-slate-600">
        근무시간
        <input type="number" step="0.25" className={fieldClass} {...form.register("work_hours")} />
        <span className="mt-1 block text-xs text-red-700">
          {form.formState.errors.work_hours?.message}
        </span>
      </label>
      <label className="text-xs font-medium text-slate-600">
        잔업시간
        <input type="number" step="0.25" className={fieldClass} {...form.register("overtime_hours")} />
        <span className="mt-1 block text-xs text-red-700">
          {form.formState.errors.overtime_hours?.message}
        </span>
      </label>
      <label className="text-xs font-medium text-slate-600">
        상태
        <select className={fieldClass} {...form.register("attendance_status")}>
          <option value="present">정상</option>
          <option value="late">지각</option>
          <option value="absent">결근</option>
          <option value="leave">휴가</option>
        </select>
      </label>
      <div className="mt-2 flex justify-end gap-2">
        <button type="button" className="rounded border border-slate-300 px-3 py-2 text-sm" onClick={onCancel}>
          취소
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="rounded bg-teal-800 px-3 py-2 text-sm text-white disabled:opacity-50"
        >
          {submitting ? "저장 중..." : "저장"}
        </button>
      </div>
    </form>
  );
}
