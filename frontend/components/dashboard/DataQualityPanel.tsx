import { DATA_QUALITY_LABELS } from "@/lib/constants";
import { formatNumber } from "@/lib/format";
import type { DataQualityResult } from "@/lib/types";

export function DataQualityPanel({ data }: { data: DataQualityResult }) {
  return (
    <section className="rounded-md border border-slate-200 bg-white p-4">
      <h2 className="text-sm font-semibold text-slate-900">Data Quality Checks</h2>
      <p className="mt-1 text-xs text-slate-500">
        실제 DB를 조회한 검사 결과입니다. constraint로 막히는 항목도 0으로 표시합니다. 점수는 산출하지
        않습니다.
      </p>
      <div className="mt-4 overflow-x-auto">
        <table className="min-w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-600">
            <tr>
              <th className="px-3 py-2 font-medium">검사 항목</th>
              <th className="px-3 py-2 text-right font-medium">건수</th>
            </tr>
          </thead>
          <tbody>
            {DATA_QUALITY_LABELS.map((item) => (
              <tr key={item.key} className="border-t border-slate-200">
                <td className="px-3 py-2 text-slate-800">{item.label}</td>
                <td className="px-3 py-2 text-right tabular-nums text-slate-900">
                  {formatNumber(data[item.key])}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
