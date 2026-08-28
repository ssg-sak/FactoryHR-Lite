"use client";

import { DefinitionTooltip } from "@/components/ui/DefinitionTooltip";
import { KPI_CARDS } from "@/lib/constants";
import { formatNumber } from "@/lib/format";
import type { DashboardSummary } from "@/lib/types";

export function KpiCard({
  label,
  value,
  unit,
  description,
  definition,
}: {
  label: string;
  value: string;
  unit: string;
  description: string;
  definition: string;
}) {
  return (
    <article className="flex min-h-[7.5rem] flex-col rounded-md border border-slate-200 bg-white px-4 py-3">
      <div className="flex items-start justify-between gap-2">
        <p className="text-sm font-medium text-slate-800">{label}</p>
        <DefinitionTooltip definition={definition} />
      </div>
      <p className="mt-2 flex items-baseline gap-1 text-slate-900">
        <span className="text-2xl font-semibold tabular-nums tracking-tight">{value}</span>
        {unit ? <span className="text-xs font-normal text-slate-500">{unit}</span> : null}
      </p>
      <p className="mt-auto pt-2 text-xs leading-5 text-slate-500">{description}</p>
    </article>
  );
}

export function formatKpi(value: number, digits = 0): string {
  return formatNumber(value, digits);
}

export function WorkforceKpiGrid({ summary }: { summary: DashboardSummary }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      {KPI_CARDS.map((card) => {
        const raw = summary[card.key];
        const value = formatNumber(raw, card.digits);
        return (
          <KpiCard
            key={card.key}
            label={card.label}
            value={value}
            unit={card.unit}
            description={card.description}
            definition={card.definition}
          />
        );
      })}
    </div>
  );
}
