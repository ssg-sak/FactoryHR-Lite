"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { api } from "@/lib/api";
import type { Employee, EmployeeWritePayload } from "@/lib/types";

const schema = z
  .object({
    employee_number: z.string().min(1, "사번을 입력하세요.").max(30),
    name: z.string().min(1, "이름을 입력하세요.").max(100),
    department_id: z.coerce.number().int().positive("부서를 선택하세요."),
    factory_id: z.coerce.number().int().positive("공장을 선택하세요."),
    production_line_id: z.string(),
    shift_id: z.coerce.number().int().positive("교대조를 선택하세요."),
    position: z.string(),
    hired_at: z.string().min(1, "입사일을 입력하세요."),
    resigned_at: z.string(),
    status: z.enum(["active", "resigned"]),
  })
  .superRefine((value, ctx) => {
    if (value.status === "active" && value.resigned_at) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["resigned_at"],
        message: "재직 직원은 퇴사일을 비워 주세요.",
      });
    }
    if (value.status === "resigned" && !value.resigned_at) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["resigned_at"],
        message: "퇴사 직원은 퇴사일이 필요합니다.",
      });
    }
    if (value.resigned_at && value.resigned_at < value.hired_at) {
      ctx.addIssue({
        code: z.ZodIssueCode.custom,
        path: ["resigned_at"],
        message: "퇴사일은 입사일보다 빠를 수 없습니다.",
      });
    }
  });

type FormValues = z.infer<typeof schema>;

const fieldClass =
  "mt-1 w-full rounded border border-slate-300 px-3 py-2 text-sm text-slate-900";

export function EmployeeForm({
  initial,
  submitting,
  error,
  onSubmit,
  onCancel,
}: {
  initial?: Employee;
  submitting: boolean;
  error: string | null;
  onSubmit: (payload: EmployeeWritePayload) => void;
  onCancel: () => void;
}) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      employee_number: initial?.employee_number ?? "",
      name: initial?.name ?? "",
      department_id: initial?.department_id ?? 0,
      factory_id: initial?.factory_id ?? 0,
      production_line_id: initial?.production_line_id ? String(initial.production_line_id) : "",
      shift_id: initial?.shift_id ?? 0,
      position: initial?.position ?? "",
      hired_at: initial?.hired_at ?? "",
      resigned_at: initial?.resigned_at ?? "",
      status: initial?.status ?? "active",
    },
  });
  const factoryId = form.watch("factory_id");
  const departments = useQuery({ queryKey: ["departments"], queryFn: api.departments });
  const factories = useQuery({ queryKey: ["factories"], queryFn: api.factories });
  const shifts = useQuery({ queryKey: ["shifts"], queryFn: api.shifts });
  const lines = useQuery({
    queryKey: ["production-lines", factoryId],
    queryFn: () => api.productionLines(factoryId || undefined),
    enabled: Boolean(factoryId),
  });

  return (
    <form
      className="grid gap-3"
      onSubmit={form.handleSubmit((values) => {
        onSubmit({
          employee_number: values.employee_number,
          name: values.name,
          department_id: Number(values.department_id),
          factory_id: Number(values.factory_id),
          production_line_id: values.production_line_id
            ? Number(values.production_line_id)
            : null,
          shift_id: Number(values.shift_id),
          position: values.position || null,
          hired_at: values.hired_at,
          resigned_at: values.resigned_at || null,
          status: values.status,
        });
      })}
    >
      {error ? (
        <p className="rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800" role="alert">
          {error}
        </p>
      ) : null}
      <div>
        <label htmlFor="employee_number" className="text-xs font-medium text-slate-600">
          사번
        </label>
        <input id="employee_number" className={fieldClass} {...form.register("employee_number")} />
        <ErrorMessage message={form.formState.errors.employee_number?.message} />
      </div>
      <div>
        <label htmlFor="name" className="text-xs font-medium text-slate-600">
          이름
        </label>
        <input id="name" className={fieldClass} {...form.register("name")} />
        <ErrorMessage message={form.formState.errors.name?.message} />
      </div>
      <div>
        <label htmlFor="department_id" className="text-xs font-medium text-slate-600">
          부서
        </label>
        <select id="department_id" className={fieldClass} {...form.register("department_id")}>
          <option value="">선택</option>
          {departments.data?.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <ErrorMessage message={form.formState.errors.department_id?.message} />
      </div>
      <div>
        <label htmlFor="factory_id" className="text-xs font-medium text-slate-600">
          공장
        </label>
        <select
          id="factory_id"
          className={fieldClass}
          {...form.register("factory_id", {
            onChange: () => form.setValue("production_line_id", ""),
          })}
        >
          <option value="">선택</option>
          {factories.data?.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <ErrorMessage message={form.formState.errors.factory_id?.message} />
      </div>
      <div>
        <label htmlFor="production_line_id" className="text-xs font-medium text-slate-600">
          생산라인
        </label>
        <select id="production_line_id" className={fieldClass} {...form.register("production_line_id")}>
          <option value="">없음</option>
          {lines.data?.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
      </div>
      <div>
        <label htmlFor="shift_id" className="text-xs font-medium text-slate-600">
          교대조
        </label>
        <select id="shift_id" className={fieldClass} {...form.register("shift_id")}>
          <option value="">선택</option>
          {shifts.data?.map((item) => (
            <option key={item.id} value={item.id}>
              {item.name}
            </option>
          ))}
        </select>
        <ErrorMessage message={form.formState.errors.shift_id?.message} />
      </div>
      <div>
        <label htmlFor="position" className="text-xs font-medium text-slate-600">
          직책
        </label>
        <input id="position" className={fieldClass} {...form.register("position")} />
      </div>
      <div>
        <label htmlFor="hired_at" className="text-xs font-medium text-slate-600">
          입사일
        </label>
        <input id="hired_at" type="date" className={fieldClass} {...form.register("hired_at")} />
        <ErrorMessage message={form.formState.errors.hired_at?.message} />
      </div>
      <div>
        <label htmlFor="status" className="text-xs font-medium text-slate-600">
          상태
        </label>
        <select id="status" className={fieldClass} {...form.register("status")}>
          <option value="active">재직</option>
          <option value="resigned">퇴사</option>
        </select>
      </div>
      <div>
        <label htmlFor="resigned_at" className="text-xs font-medium text-slate-600">
          퇴사일
        </label>
        <input id="resigned_at" type="date" className={fieldClass} {...form.register("resigned_at")} />
        <ErrorMessage message={form.formState.errors.resigned_at?.message} />
      </div>
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

function ErrorMessage({ message }: { message?: string }) {
  if (!message) {
    return null;
  }
  return <span className="mt-1 block text-xs text-red-700">{message}</span>;
}
