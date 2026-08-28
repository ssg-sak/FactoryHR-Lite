"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { AttendanceLines, ChartCard, HorizontalBars, VerticalBars } from "@/components/charts/Charts";
import { DataQualityPanel } from "@/components/dashboard/DataQualityPanel";
import { KpiCard, formatKpi } from "@/components/dashboard/KpiCard";
import { FilterBar } from "@/components/filters/FilterBar";
import { AppShell } from "@/components/layout/AppShell";
import { ErrorState, Spinner } from "@/components/ui/Feedback";
import { api, reportDownloadUrl } from "@/lib/api";
import { DEFAULT_DATE_FROM, DEFAULT_DATE_TO, KPI_DEFINITIONS } from "@/lib/constants";
import { ApiError } from "@/lib/errors";
import { formatPercent } from "@/lib/format";
import type { AIReportResponse, WorkforceFilters } from "@/lib/types";

const INITIAL_FILTERS: WorkforceFilters = {
  date_from: DEFAULT_DATE_FROM,
  date_to: DEFAULT_DATE_TO,
};

export default function ReportsPage() {
  const [filters, setFilters] = useState<WorkforceFilters>(INITIAL_FILTERS);
  const queryFilters = useMemo(() => filters, [filters]);
  const [ai, setAi] = useState<AIReportResponse | null>(null);

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
  const quality = useQuery({ queryKey: ["data-quality"], queryFn: api.dataQuality });
  const aiMutation = useMutation({
    mutationFn: () => api.aiSummary(queryFilters),
    onSuccess: setAi,
  });

  return (
    <AppShell title="Reports" description="필터를 적용한 리포트 미리보기, PDF/CSV 다운로드, AI 요약">
      <div className="space-y-5">
        <FilterBar value={filters} onChange={setFilters} onReset={() => setFilters(INITIAL_FILTERS)} />
        <div className="flex flex-wrap gap-2">
          <a
            className="rounded bg-teal-800 px-3 py-2 text-sm text-white"
            href={reportDownloadUrl("/api/reports/workforce.pdf", filters)}
          >
            PDF 다운로드
          </a>
          <a
            className="rounded border border-slate-300 bg-white px-3 py-2 text-sm"
            href={reportDownloadUrl("/api/reports/employees.csv", filters)}
          >
            직원 CSV
          </a>
          <a
            className="rounded border border-slate-300 bg-white px-3 py-2 text-sm"
            href={reportDownloadUrl("/api/reports/attendance.csv", filters)}
          >
            근태 CSV
          </a>
          <button
            type="button"
            className="rounded border border-slate-300 bg-white px-3 py-2 text-sm disabled:opacity-50"
            disabled={aiMutation.isPending}
            onClick={() => aiMutation.mutate()}
          >
            {aiMutation.isPending ? "AI 요약 생성 중..." : "AI Summary 생성"}
          </button>
        </div>
        {aiMutation.error instanceof ApiError ? (
          <ErrorState message={aiMutation.error.message} />
        ) : null}

        {summary.isLoading ? <Spinner /> : null}
        {summary.error instanceof Error ? <ErrorState message={summary.error.message} /> : null}

        <section className="space-y-3">
          <h2 className="text-sm font-semibold text-slate-900">Report Preview · KPI Summary</h2>
          {summary.data ? (
            <div className="grid gap-4 md:grid-cols-3">
              <KpiCard
                label="현재 재직 인원"
                value={formatKpi(summary.data.active_employees)}
                unit="명"
                definition={KPI_DEFINITIONS.active_employees}
              />
              <KpiCard
                label="선택 기간 퇴사 인원"
                value={formatKpi(summary.data.resigned_in_period)}
                unit="명"
                definition={KPI_DEFINITIONS.resigned_in_period}
              />
              <KpiCard
                label="평균 잔업시간"
                value={formatKpi(summary.data.average_overtime_hours, 2)}
                unit="시간"
                definition={KPI_DEFINITIONS.average_overtime_hours}
              />
              <KpiCard
                label="결근 기록 비율"
                value={formatPercent(summary.data.absence_rate)}
                unit=""
                definition={KPI_DEFINITIONS.absence_rate}
              />
              <KpiCard
                label="지각 기록 비율"
                value={formatPercent(summary.data.late_rate)}
                unit=""
                definition={KPI_DEFINITIONS.late_rate}
              />
              <KpiCard
                label="평균 근속 개월"
                value={formatKpi(summary.data.average_tenure_months, 1)}
                unit="개월"
                definition={KPI_DEFINITIONS.average_tenure_months}
              />
            </div>
          ) : null}
        </section>

        <section className="grid gap-4 xl:grid-cols-2">
          <ChartCard title="Workforce Structure" description="재직 인원 공장 분포" unit="명">
            <HorizontalBars data={workforce.data?.active_by_factory ?? []} />
          </ChartCard>
          <ChartCard title="Attendance" description="날짜별 결근/지각 비율" unit="%">
            <AttendanceLines data={trend.data?.points ?? []} />
          </ChartCard>
          <ChartCard title="Overtime" description="교대조별 평균 잔업" unit="시간">
            <VerticalBars data={overtime.data?.by_shift ?? []} valueKey="average_overtime_hours" />
          </ChartCard>
          {quality.data ? <DataQualityPanel data={quality.data} /> : null}
        </section>

        <section className="rounded-md border border-slate-200 bg-white p-4">
          <h2 className="text-sm font-semibold text-slate-900">AI Summary</h2>
          <p className="mt-1 text-xs text-slate-500">
            Gemini는 위에서 계산된 KPI JSON만 받습니다. API key가 없으면 이 버튼만 실패하고 PDF/CSV는 그대로
            동작합니다.
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
      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
      <ul className="mt-2 list-disc space-y-1 pl-4 text-sm text-slate-800">
        {items.length ? items.map((item) => <li key={item}>{item}</li>) : <li>해당 항목 없음</li>}
      </ul>
    </div>
  );
}
