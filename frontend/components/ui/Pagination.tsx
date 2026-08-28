export function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
}: {
  page: number;
  pageSize: number;
  total: number;
  onPageChange: (page: number) => void;
}) {
  const pageCount = Math.max(1, Math.ceil(total / pageSize));
  return (
    <div className="flex items-center justify-between gap-3 text-sm text-slate-600">
      <p>
        총 {total.toLocaleString("ko-KR")}건 · {page}/{pageCount} 페이지
      </p>
      <div className="flex gap-2">
        <button
          type="button"
          className="rounded border border-slate-300 bg-white px-3 py-1 disabled:text-slate-400"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          이전
        </button>
        <button
          type="button"
          className="rounded border border-slate-300 bg-white px-3 py-1 disabled:text-slate-400"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= pageCount}
        >
          다음
        </button>
      </div>
    </div>
  );
}
