import { formatNumber } from "@/lib/format";

export function KpiCard({
  label,
  value,
  unit,
  definition,
}: {
  label: string;
  value: string;
  unit: string;
  definition: string;
}) {
  return (
    <article className="rounded-md border border-slate-200 bg-white p-4" title={definition}>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-2 text-2xl font-semibold tabular-nums text-slate-900">
        {value}
        <span className="ml-1 text-sm font-normal text-slate-500">{unit}</span>
      </p>
      <p className="mt-2 text-xs leading-5 text-slate-500">{definition}</p>
    </article>
  );
}

export function formatKpi(value: number, digits = 0): string {
  return formatNumber(value, digits);
}
