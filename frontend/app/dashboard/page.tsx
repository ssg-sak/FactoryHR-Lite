"use client";

import { useQuery } from "@tanstack/react-query";
import { AttendanceLines, ChartCard, HorizontalBars, VerticalBars } from "@/components/charts/Charts";
import { DataQualityPanel } from "@/components/dashboard/DataQualityPanel";
import { WorkforceKpiGrid } from "@/components/dashboard/KpiCard";
import { FilterBar } from "@/components/filters/FilterBar";
import { useWorkforceFilters } from "@/components/filters/WorkforceFilterContext";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorState, Spinner } from "@/components/ui/Feedback";
import { api } from "@/lib/api";
import { KPI_DEFINITIONS } from "@/lib/constants";

export default function DashboardPage() {
  const { filters, setFilters, resetFilters } = useWorkforceFilters();
  const summary = useQuery({
    queryKey: ["dashboard-summary", filters],
    queryFn: () => api.dashboardSummary(filters),
  });
  const workforce = useQuery({
    queryKey: ["workforce", filters],
    queryFn: () => api.workforceDistribution(filters),
  });
  const trend = useQuery({
    queryKey: ["attendance-trend", filters],
    queryFn: () => api.attendanceTrend(filters),
  });
  const overtime = useQuery({
    queryKey: ["overtime", filters],
    queryFn: () => api.overtime(filters),
  });
  const tenure = useQuery({
    queryKey: ["tenure", filters],
    queryFn: () => api.tenure(filters),
  });
  const quality = useQuery({ queryKey: ["data-quality"], queryFn: api.dataQuality });

  return (
    <AppShell
      title="대시보드"
      description="조회 조건 기준으로 재직·근태·잔업 현황을 확인합니다."
    >
      <div className="space-y-4">
        <FilterBar value={filters} onChange={setFilters} onReset={resetFilters} />
        {quality.data ? <DataQualityPanel data={quality.data} /> : null}
        {summary.isLoading ? <Spinner /> : null}
        {summary.error instanceof Error ? <ErrorState message={summary.error.message} /> : null}
        {summary.data ? (
          <section className="space-y-3">
            <h2 className="text-sm font-semibold text-slate-800">핵심 지표</h2>
            <WorkforceKpiGrid summary={summary.data} />
          </section>
        ) : null}

        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-800">인력 구성</h2>
          <div className="grid gap-3 xl:grid-cols-2">
            <ChartCard
              title="공장별 재직 인원"
              description="현재 재직 직원 수"
              definition="현재 status = active인 직원 수. 과거 배치 이력은 포함하지 않습니다."
              unit="명"
            >
              <HorizontalBars data={workforce.data?.active_by_factory ?? []} />
            </ChartCard>
            <ChartCard
              title="생산라인별 재직 인원"
              description="생산라인이 지정된 재직 직원"
              definition="생산라인이 지정된 재직 직원만 해당 라인에 집계됩니다."
              unit="명"
            >
              <HorizontalBars data={workforce.data?.active_by_line ?? []} />
            </ChartCard>
            <ChartCard
              title="교대조별 재직 인원"
              description="현재 교대 배치 기준"
              definition="현재 교대 배치 기준 재직 인원입니다."
              unit="명"
            >
              <VerticalBars data={workforce.data?.active_by_shift ?? []} />
            </ChartCard>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-800">근태 및 잔업</h2>
          <div className="grid gap-3 xl:grid-cols-2">
            <ChartCard
              title="근태 추이"
              description="날짜별 결근·지각 비율"
              definition={
                `${KPI_DEFINITIONS.absence_rate}\n${KPI_DEFINITIONS.late_rate}`
              }
              unit="%"
            >
              <AttendanceLines data={trend.data?.points ?? []} />
            </ChartCard>
            <ChartCard
              title="라인별 평균 잔업시간"
              description="선택 기간 평균 잔업시간"
              definition="선택 기간 attendance.overtime_hours 평균. 직원 현재 라인 기준입니다."
              unit="시간"
            >
              <VerticalBars
                data={overtime.data?.by_production_line ?? []}
                valueKey="average_overtime_hours"
              />
            </ChartCard>
            <ChartCard
              title="교대조별 평균 잔업시간"
              description="선택 기간 평균 잔업시간"
              definition="선택 기간 attendance.overtime_hours 평균. 직원 현재 교대 기준입니다."
              unit="시간"
            >
              <VerticalBars data={overtime.data?.by_shift ?? []} valueKey="average_overtime_hours" />
            </ChartCard>
          </div>
        </section>

        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-800">근속 및 인력 변화</h2>
          <div className="grid gap-3 xl:grid-cols-2">
            <ChartCard
              title="근속기간 분포"
              description="재직 직원 기준"
              definition={tenure.data?.definition || KPI_DEFINITIONS.average_tenure_months}
              unit="명"
            >
              <VerticalBars data={tenure.data?.bands ?? []} nameKey="label" />
            </ChartCard>
            <ChartCard
              title="부서별 기간 내 퇴사 인원"
              description="선택 기간 퇴사 인원"
              definition="부서별 퇴사 인원입니다. 평균 재직 분모가 없어 turnover rate로 해석하지 않습니다."
              unit="명"
            >
              <VerticalBars data={workforce.data?.resignations_by_department ?? []} />
            </ChartCard>
          </div>
        </section>
      </div>
    </AppShell>
  );
}
