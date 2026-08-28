"use client";

import { EmptyState } from "@/components/ui/Feedback";
import { DefinitionTooltip } from "@/components/ui/DefinitionTooltip";
import { hasChartValues } from "@/lib/format";
import type { ReactNode } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export function ChartCard({
  title,
  description,
  definition,
  unit,
  children,
}: {
  title: string;
  description?: string;
  definition?: string;
  unit: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <div className="mb-3 flex items-start justify-between gap-2">
        <div className="min-w-0">
          <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
          {description ? <p className="mt-1 text-xs text-slate-500">{description}</p> : null}
          <p className="mt-0.5 text-[11px] text-slate-400">단위: {unit}</p>
        </div>
        {definition ? <DefinitionTooltip definition={definition} /> : null}
      </div>
      {children}
    </section>
  );
}

const tooltipStyle = {
  fontSize: 12,
  border: "1px solid #d7dee4",
  borderRadius: 4,
};

type ChartRow = {
  name?: string;
  label?: string;
  count?: number;
  average_overtime_hours?: number;
};

export function HorizontalBars({
  data,
  nameKey = "name",
  valueKey = "count",
}: {
  data: ChartRow[];
  nameKey?: "name" | "label";
  valueKey?: "count" | "average_overtime_hours";
}) {
  const values = data.map((item) => Number(item[valueKey] ?? 0));
  if (!hasChartValues(values)) {
    return <EmptyState message="선택한 조건에 해당하는 데이터가 없습니다." />;
  }
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 16, right: 16 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis type="number" />
          <YAxis type="category" dataKey={nameKey} width={92} tick={{ fontSize: 12 }} />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey={valueKey} fill="#1f4e5f" radius={[0, 3, 3, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function VerticalBars({
  data,
  nameKey = "name",
  valueKey = "count",
}: {
  data: ChartRow[];
  nameKey?: "name" | "label";
  valueKey?: "count" | "average_overtime_hours";
}) {
  const values = data.map((item) => Number(item[valueKey] ?? 0));
  if (!hasChartValues(values)) {
    return <EmptyState message="선택한 조건에 해당하는 데이터가 없습니다." />;
  }
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 8, right: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey={nameKey} tick={{ fontSize: 12 }} />
          <YAxis />
          <Tooltip contentStyle={tooltipStyle} />
          <Bar dataKey={valueKey} fill="#1f4e5f" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function AttendanceLines({
  data,
}: {
  data: Array<{
    work_date: string;
    absence_rate: number;
    late_rate: number;
    total: number;
  }>;
}) {
  if (!data.length) {
    return <EmptyState message="선택한 조건에 해당하는 데이터가 없습니다." />;
  }
  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ left: 8, right: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
          <XAxis dataKey="work_date" tick={{ fontSize: 11 }} />
          <YAxis unit="%" />
          <Tooltip contentStyle={tooltipStyle} />
          <Legend />
          <Line
            type="monotone"
            dataKey="absence_rate"
            name="결근 비율"
            stroke="#b45309"
            dot={false}
            strokeWidth={2}
          />
          <Line
            type="monotone"
            dataKey="late_rate"
            name="지각 비율"
            stroke="#1f4e5f"
            dot={false}
            strokeWidth={2}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
