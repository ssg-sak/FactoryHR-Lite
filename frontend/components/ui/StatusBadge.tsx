import { ATTENDANCE_STATUS_LABEL, EMPLOYEE_STATUS_LABEL } from "@/lib/constants";

export function StatusBadge({
  kind,
  value,
}: {
  kind: "employee" | "attendance";
  value: string;
}) {
  const label =
    kind === "employee"
      ? EMPLOYEE_STATUS_LABEL[value] ?? value
      : ATTENDANCE_STATUS_LABEL[value] ?? value;
  const tone =
    value === "active" || value === "present"
      ? "bg-emerald-50 text-emerald-800 border-emerald-200"
      : value === "late"
        ? "bg-amber-50 text-amber-800 border-amber-200"
        : value === "absent" || value === "resigned"
          ? "bg-rose-50 text-rose-800 border-rose-200"
          : "bg-slate-100 text-slate-700 border-slate-200";
  return (
    <span className={`inline-flex items-center rounded border px-2 py-0.5 text-xs ${tone}`}>
      {label}
    </span>
  );
}
