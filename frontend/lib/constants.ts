export const DEFAULT_DATE_FROM = "2026-07-29";
export const DEFAULT_DATE_TO = "2026-08-27";

export const ATTENDANCE_STATUS_LABEL: Record<string, string> = {
  present: "정상",
  late: "지각",
  absent: "결근",
  leave: "휴가",
};

export const EMPLOYEE_STATUS_LABEL: Record<string, string> = {
  active: "재직",
  resigned: "퇴사",
};

export const KPI_DEFINITIONS = {
  active_employees: "현재 status=active인 직원 수",
  resigned_in_period: "status=resigned이고 resigned_at이 선택 기간에 포함된 직원 수",
  average_tenure_months:
    "근속일수 / 30.4375. 재직: report date − hired_at, 퇴사: resigned_at − hired_at",
  average_overtime_hours: "선택 기간 attendance.overtime_hours 평균",
  absence_rate: "선택 기간 attendance records 중 attendance_status=absent 비율(%)",
  late_rate: "선택 기간 attendance records 중 attendance_status=late 비율(%)",
};

export const DATA_QUALITY_LABELS: { key: keyof import("./types").DataQualityResult; label: string }[] =
  [
    { key: "total_employees", label: "Employees" },
    { key: "total_attendance_records", label: "Attendance Records" },
    { key: "duplicate_employee_numbers", label: "Duplicate Employee Numbers" },
    { key: "duplicate_attendance", label: "Duplicate Employee-Date Attendance" },
    { key: "invalid_work_hours", label: "Invalid Work Hours" },
    { key: "invalid_overtime_hours", label: "Invalid Overtime Hours" },
    { key: "attendance_before_hire_date", label: "Attendance Before Hire Date" },
    { key: "attendance_after_resignation", label: "Attendance After Resignation" },
    { key: "factory_line_mismatch", label: "Factory-Line Mismatch" },
  ];
