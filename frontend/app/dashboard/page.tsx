"use client";

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { AttendanceLines, ChartCard, HorizontalBars, VerticalBars } from "@/components/charts/Charts";
import { DataQualityPanel } from "@/components/dashboard/DataQualityPanel";
import { KpiCard, formatKpi } from "@/components/dashboard/KpiCard";
import { FilterBar } from "@/components/filters/FilterBar";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorState, Spinner } from "@/components/ui/Feedback";
import { api } from "@/lib/api";
import { KPI_DEFINITIONS, DEFAULT_DATE_FROM, DEFAULT_DATE_TO } from "@/lib/constants";
import { formatPercent } from "@/lib/format";
import type { WorkforceFilters } from "@/lib/types";

const INITIAL_FILTERS: WorkforceFilters = {
  date_from: DEFAULT_DATE_FROM,
  date_to: DEFAULT_DATE_TO,
};

export default function DashboardPage() {
  const [filters, setFilters] = useState<WorkforceFilters>(INITIAL_FILTERS);
  const queryFilters = useMemo(() => filters, [filters]);
  const summary = useQuery({
    queryKey: ["dashboard-summary", queryFilters],
    queryFn: () => api.dashboardSummary(queryFilters),
  });
  const workforce = useQuery({
    queryKey: ["workforce", queryFilters],
    queryFn: () => api.workforceDistribution(queryFilters),
  });
  const trend = useQuery({
    queryKey: ["attendance-trend", queryFilters],
    queryFn: () => api.attendanceTrend(queryFilters),
  });
  const overtime = useQuery({
    queryKey: ["overtime", queryFilters],
    queryFn: () => api.overtime(queryFilters),
  });
  const tenure = useQuery({
    queryKey: ["tenure", queryFilters],
    queryFn: () => api.tenure(queryFilters),
  });
  const quality = useQuery({ queryKey: ["data-quality"], queryFn: api.dataQuality });

  return (
    <AppShell
      title="Dashboard"
      description="선택 기간과 조직 필터 기준으로 재직·근태·잔업 지표를 표시합니다."
    >
      <div className="space-y-5">
        <FilterBar
          value={filters}
          onChange={setFilters}
          onReset={() => setFilters(INITIAL_FILTERS)}
        />
        {summary.isLoading ? <Spinner /> : null}
        {summary.error instanceof Error ? <ErrorState message={summary.error.message} /> : null}
        {summary.data ? (
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <KpiCard
              label="현재 재직 인원"
              value={formatKpi(summary.data.active_employees)}
              unit="명"
              definition={summary.data.metric_definitions.active_employees ?? KPI_DEFINITIONS.active_employees}
            />
            <KpiCard
              label="선택 기간 퇴사 인원"
              value={formatKpi(summary.data.resigned_in_period)}
              unit="명"
              definition={
                summary.data.metric_definitions.resigned_in_period ?? KPI_DEFINITIONS.resigned_in_period
              }
            />
            <KpiCard
              label="평균 근속 개월"
              value={formatKpi(summary.data.average_tenure_months, 1)}
              unit="개월"
              definition={
                summary.data.metric_definitions.average_tenure_months ??
                KPI_DEFINITIONS.average_tenure_months
              }
            />
            <KpiCard
              label="평균 잔업시간"
              value={formatKpi(summary.data.average_overtime_hours, 2)}
              unit="시간"
              definition={
                summary.data.metric_definitions.average_overtime_hours ??
                KPI_DEFINITIONS.average_overtime_hours
              }
            />
            <KpiCard
              label="결근 기록 비율"
              value={formatPercent(summary.data.absence_rate)}
              unit=""
              definition={summary.data.metric_definitions.absence_rate ?? KPI_DEFINITIONS.absence_rate}
            />
            <KpiCard
              label="지각 기록 비율"
              value={formatPercent(summary.data.late_rate)}
              unit=""
              definition={summary.data.metric_definitions.late_rate ?? KPI_DEFINITIONS.late_rate}
            />
          </div>
        ) : null}

        <div className="grid gap-4 xl:grid-cols-2">
          <ChartCard
            title="공장별 재직인원"
            description="현재 status=active 직원 수. 과거 배치 이력은 포함하지 않습니다."
            unit="명"
          >
            <HorizontalBars data={workforce.data?.active_by_factory ?? []} />
          </ChartCard>
          <ChartCard
            title="생산라인별 재직인원"
            description="생산라인이 지정된 재직 직원만 해당 라인에 집계됩니다."
            unit="명"
          >
            <HorizontalBars data={workforce.data?.active_by_line ?? []} />
          </ChartCard>
          <ChartCard
            title="교대조별 재직인원"
            description="현재 교대 배치 기준 재직 인원입니다."
            unit="명"
          >
            <VerticalBars data={workforce.data?.active_by_shift ?? []} />
          </ChartCard>
          <ChartCard
            title="날짜별 근태 추이"
            description="해당 날짜 attendance records 중 결근/지각 비율입니다."
            unit="%"
          >
            <AttendanceLines data={trend.data?.points ?? []} />
          </ChartCard>
          <ChartCard
            title="생산라인별 평균 잔업"
            description="선택 기간 attendance.overtime_hours 평균. 직원 현재 라인 기준입니다."
            unit="시간"
          >
            <VerticalBars
              data={overtime.data?.by_production_line ?? []}
              valueKey="average_overtime_hours"
            />
          </ChartCard>
          <ChartCard
            title="교대조별 평균 잔업"
            description="선택 기간 attendance.overtime_hours 평균. 직원 현재 교대 기준입니다."
            unit="시간"
          >
            <VerticalBars data={overtime.data?.by_shift ?? []} valueKey="average_overtime_hours" />
          </ChartCard>
          <ChartCard
            title="근속기간 분포"
            description={tenure.data?.definition ?? "재직 직원만 포함합니다."}
            unit="명"
          >
            <VerticalBars data={tenure.data?.bands ?? []} nameKey="label" />
          </ChartCard>
          <ChartCard
            title="기간 내 퇴사인원"
            description="부서별 퇴사 인원입니다. 평균 재직 분모가 없어 turnover rate로 해석하지 않습니다."
            unit="명"
          >
            <VerticalBars data={workforce.data?.resignations_by_department ?? []} />
          </ChartCard>
        </div>
        {quality.data ? <DataQualityPanel data={quality.data} /> : null}
      </div>
    </AppShell>
  );
}
