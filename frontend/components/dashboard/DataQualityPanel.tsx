"use client";

import { CheckCircle2, CircleAlert } from "lucide-react";
import { DATA_QUALITY_CHECKS } from "@/lib/constants";
import { formatNumber } from "@/lib/format";
import type { DataQualityResult } from "@/lib/types";

export function dataQualityViolationCount(data: DataQualityResult): number {
  return DATA_QUALITY_CHECKS.reduce((sum, item) => sum + (data[item.key] || 0), 0);
}

export function DataQualityPanel({ data }: { data: DataQualityResult }) {
  const checkCount = DATA_QUALITY_CHECKS.length;
  const violations = dataQualityViolationCount(data);
  const passed = violations === 0;

  return (
    <details className="rounded-md border border-slate-200 bg-white">
      <summary className="flex cursor-pointer list-none items-start justify-between gap-4 px-4 py-3 marker:content-none [&::-webkit-details-marker]:hidden">
        <div className="min-w-0">
          <p className="text-sm font-medium text-slate-800">데이터 검증 상태</p>
          <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-600">
            {passed ? (
              <CheckCircle2 size={16} className="shrink-0 text-teal-700" aria-hidden="true" />
            ) : (
              <CircleAlert size={16} className="shrink-0 text-amber-600" aria-hidden="true" />
            )}
            <span>{passed ? "주요 정합성 검사 통과" : `검증 필요 ${formatNumber(violations)}건`}</span>
          </p>
          <p className="mt-1 text-xs text-slate-500">
            {checkCount}개 항목 확인 · 위반 {formatNumber(violations)}건
          </p>
        </div>
        <span className="shrink-0 pt-0.5 text-xs font-medium text-slate-500">상세 보기</span>
      </summary>
      <div className="border-t border-slate-200 px-4 py-3">
        <p className="mb-3 text-xs text-slate-500">
          실제 DB 조회 결과입니다. 점수는 산출하지 않습니다.
        </p>
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-3 py-2 font-medium">검사 항목</th>
              <th className="px-3 py-2 text-right font-medium">건수</th>
            </tr>
          </thead>
          <tbody>
            {DATA_QUALITY_CHECKS.map((item) => {
              const count = data[item.key];
              return (
                <tr key={item.key} className="border-t border-slate-200">
                  <td className="px-3 py-2 text-slate-800">{item.label}</td>
                  <td
                    className={`px-3 py-2 text-right tabular-nums ${
                      count > 0 ? "font-medium text-amber-700" : "text-slate-900"
                    }`}
                  >
                    {formatNumber(count)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </details>
  );
}
