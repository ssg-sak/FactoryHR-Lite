"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/format";
import type { WorkforceFilters } from "@/lib/types";

const selectClass =
  "rounded border border-slate-300 bg-white px-2 py-1.5 text-sm text-slate-800";

export function FilterBar({
  value,
  onChange,
  onReset,
  showDates = true,
}: {
  value: WorkforceFilters;
  onChange: (next: WorkforceFilters) => void;
  onReset: () => void;
  showDates?: boolean;
}) {
  const departments = useQuery({ queryKey: ["departments"], queryFn: api.departments });
  const factories = useQuery({ queryKey: ["factories"], queryFn: api.factories });
  const shifts = useQuery({ queryKey: ["shifts"], queryFn: api.shifts });
  const lines = useQuery({
    queryKey: ["production-lines", value.factory_id],
    queryFn: () => api.productionLines(value.factory_id),
  });

  const factoryName = factories.data?.find((item) => item.id === value.factory_id)?.name;
  const deptName = departments.data?.find((item) => item.id === value.department_id)?.name;
  const lineName = lines.data?.find((item) => item.id === value.production_line_id)?.name;
  const shiftName = shifts.data?.find((item) => item.id === value.shift_id)?.name;
  const periodLabel =
    value.date_from || value.date_to
      ? `${formatDate(value.date_from)} ~ ${formatDate(value.date_to)}`
      : "전체";
  const orgChips = [
    `부서 ${deptName ?? "전체"}`,
    `공장 ${factoryName ?? "전체"}`,
    `생산라인 ${lineName ?? "전체"}`,
    `교대조 ${shiftName ?? "전체"}`,
  ];

  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-start justify-between gap-3">
        <h2 className="text-sm font-semibold text-slate-800">조회 조건</h2>
        <button
          type="button"
          onClick={onReset}
          className="rounded border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700"
        >
          초기화
        </button>
      </div>
      <div className={`grid gap-3 md:grid-cols-3 ${showDates ? "xl:grid-cols-6" : "xl:grid-cols-4"}`}>
        {showDates ? (
          <>
            <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
              시작일
              <input
                type="date"
                className={selectClass}
                value={value.date_from ?? ""}
                onChange={(event) => onChange({ ...value, date_from: event.target.value || undefined })}
              />
            </label>
            <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
              종료일
              <input
                type="date"
                className={selectClass}
                value={value.date_to ?? ""}
                onChange={(event) => onChange({ ...value, date_to: event.target.value || undefined })}
              />
            </label>
          </>
        ) : null}
        <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
          부서
          <select
            className={selectClass}
            value={value.department_id ?? ""}
            onChange={(event) =>
              onChange({
                ...value,
                department_id: event.target.value ? Number(event.target.value) : undefined,
              })
            }
          >
            <option value="">전체</option>
            {departments.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <label htmlFor="filter-factory" className="flex flex-col gap-1 text-xs font-medium text-slate-600">
          공장
          <select
            id="filter-factory"
            className={selectClass}
            value={value.factory_id ?? ""}
            onChange={(event) =>
              onChange({
                ...value,
                factory_id: event.target.value ? Number(event.target.value) : undefined,
                production_line_id: undefined,
              })
            }
          >
            <option value="">전체</option>
            {factories.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
          생산라인
          <select
            className={selectClass}
            value={value.production_line_id ?? ""}
            onChange={(event) =>
              onChange({
                ...value,
                production_line_id: event.target.value ? Number(event.target.value) : undefined,
              })
            }
          >
            <option value="">전체</option>
            {lines.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1 text-xs font-medium text-slate-600">
          교대조
          <select
            className={selectClass}
            value={value.shift_id ?? ""}
            onChange={(event) =>
              onChange({
                ...value,
                shift_id: event.target.value ? Number(event.target.value) : undefined,
              })
            }
          >
            <option value="">전체</option>
            {shifts.data?.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
      </div>
      <div className="mt-3 space-y-1 text-sm text-slate-600" data-testid="filter-summary">
        {showDates ? (
          <p>
            <span className="text-slate-500">조회 기간</span> {periodLabel}
          </p>
        ) : null}
        <p>{orgChips.join(" · ")}</p>
      </div>
    </section>
  );
}
