"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Sparkles } from "lucide-react";
import { useState } from "react";
import { AttendanceLines, ChartCard, HorizontalBars, VerticalBars } from "@/components/charts/Charts";
import { DataQualityPanel } from "@/components/dashboard/DataQualityPanel";
import { WorkforceKpiGrid } from "@/components/dashboard/KpiCard";
import { FilterBar } from "@/components/filters/FilterBar";
import { useWorkforceFilters } from "@/components/filters/WorkforceFilterContext";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorState, Spinner } from "@/components/ui/Feedback";
import { api, downloadReport } from "@/lib/api";
import { KPI_DEFINITIONS } from "@/lib/constants";
import { ApiError } from "@/lib/errors";
import type { AIReportResponse } from "@/lib/types";

export default function ReportsPage() {
  const { filters, setFilters, resetFilters } = useWorkforceFilters();
  const [ai, setAi] = useState<AIReportResponse | null>(null);

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
  const aiMutation = useMutation({
    mutationFn: () => api.aiSummary(filters),
    onSuccess: setAi,
  });

  return (
    <AppShell
      title="리포트"
      description="조회 조건을 적용해 인력운영 지표를 확인하고 PDF/CSV 리포트를 내려받을 수 있습니다."
    >
      <div className="space-y-4">
        <FilterBar value={filters} onChange={setFilters} onReset={resetFilters} />
        {quality.data ? <DataQualityPanel data={quality.data} /> : null}

        <section className="rounded-md border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              className="rounded bg-teal-800 px-3.5 py-2 text-sm font-medium text-white"
              onClick={() => {
                void downloadReport("/api/reports/workforce.pdf", filters);
              }}
            >
              PDF 리포트 다운로드
            </button>
            <button
              type="button"
              className="rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
              onClick={() => {
                void downloadReport("/api/reports/employees.csv", filters);
              }}
            >
              직원 CSV
            </button>
            <button
              type="button"
              className="rounded border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
              onClick={() => {
                void downloadReport("/api/reports/attendance.csv", filters);
              }}
            >
              근태 CSV
            </button>
            <span className="hidden h-6 w-px bg-slate-200 sm:block" aria-hidden="true" />
            <button
              type="button"
              className="inline-flex items-center gap-1.5 rounded border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-800 disabled:opacity-50"
              disabled={aiMutation.isPending}
              onClick={() => aiMutation.mutate()}
            >
              <Sparkles size={14} aria-hidden="true" />
              {aiMutation.isPending ? "AI 요약 생성 중..." : "AI 요약 생성"}
            </button>
          </div>
        </section>
        {aiMutation.error instanceof ApiError ? (
          <ErrorState message={aiMutation.error.message} />
        ) : null}

        {summary.isLoading ? <Spinner /> : null}
        {summary.error instanceof Error ? <ErrorState message={summary.error.message} /> : null}

        <section className="space-y-3">
          <div>
            <h2 className="text-sm font-semibold text-slate-800">리포트 미리보기</h2>
            <p className="mt-0.5 text-xs text-slate-500">핵심 지표</p>
          </div>
          {summary.data ? <WorkforceKpiGrid summary={summary.data} /> : null}
        </section>

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
              definition={`${KPI_DEFINITIONS.absence_rate}\n${KPI_DEFINITIONS.late_rate}`}
              unit="%"
            >
              <AttendanceLines data={trend.data?.points ?? []} />
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

        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-slate-800">AI 요약</h2>
          <p className="mt-1 text-xs text-slate-500">
            위에서 계산된 핵심 지표를 바탕으로 보조 분석을 생성합니다. API key가 없으면 이 기능만
            실패하고 PDF/CSV는 그대로 동작합니다.
          </p>
          {ai ? (
            <div className="mt-4 grid gap-4 md:grid-cols-3">
              <AiColumn title="관찰된 패턴" items={ai.observations} />
              <AiColumn title="추가 확인 데이터" items={ai.additional_data_needed} />
              <AiColumn title="판단할 수 없는 내용" items={ai.cannot_conclude} />
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-500">아직 생성된 요약이 없습니다.</p>
          )}
        </section>
      </div>
    </AppShell>
  );
}

function AiColumn({ title, items }: { title: string; items: string[] }) {
  return (
    <div>
      <h3 className="text-xs font-semibold text-slate-500">{title}</h3>
      <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-slate-800">
        {items.length ? items.map((item) => <li key={item}>{item}</li>) : <li>해당 항목 없음</li>}
      </ul>
    </div>
  );
}
