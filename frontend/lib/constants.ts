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
  active_employees: "status = active인 직원 수",
  resigned_in_period:
    "status = resigned이고 resigned_at이 선택 기간 [date_from, date_to]에 포함된 직원 수",
  average_tenure_months:
    "재직(active): report_date − hired_at\n퇴사(resigned): resigned_at − hired_at\n근속일수 / 30.4375\nreport_date는 date_to, 없으면 CURRENT_DATE",
  average_overtime_hours: "선택 기간 attendance.overtime_hours의 산술평균",
  absence_rate:
    "attendance_status = absent인 row 수 / 선택 기간 전체 attendance row 수 × 100",
  late_rate: "attendance_status = late인 row 수 / 선택 기간 전체 attendance row 수 × 100",
};

export const KPI_CARDS = [
  {
    key: "active_employees",
    label: "현재 재직 인원",
    description: "현재 재직 상태인 직원 수",
    unit: "명",
    digits: 0,
    definition: KPI_DEFINITIONS.active_employees,
  },
  {
    key: "resigned_in_period",
    label: "선택 기간 퇴사 인원",
    description: "선택 기간에 퇴사 처리된 직원 수",
    unit: "명",
    digits: 0,
    definition: KPI_DEFINITIONS.resigned_in_period,
  },
  {
    key: "average_overtime_hours",
    label: "평균 잔업시간",
    description: "선택 기간의 근태 기록 기준 평균 잔업시간",
    unit: "시간",
    digits: 2,
    definition: KPI_DEFINITIONS.average_overtime_hours,
  },
  {
    key: "absence_rate",
    label: "결근 기록 비율",
    description: "선택 기간의 근태 기록 중 결근으로 기록된 비율",
    unit: "%",
    digits: 2,
    definition: KPI_DEFINITIONS.absence_rate,
  },
  {
    key: "late_rate",
    label: "지각 기록 비율",
    description: "선택 기간의 근태 기록 중 지각으로 기록된 비율",
    unit: "%",
    digits: 2,
    definition: KPI_DEFINITIONS.late_rate,
  },
  {
    key: "average_tenure_months",
    label: "평균 근속개월",
    description: "직원별 근속기간을 월 단위로 환산한 평균",
    unit: "개월",
    digits: 1,
    definition: KPI_DEFINITIONS.average_tenure_months,
  },
] as const;

export const DATA_QUALITY_CHECKS: {
  key: keyof import("./types").DataQualityResult;
  label: string;
}[] = [
  { key: "duplicate_employee_numbers", label: "중복 사번" },
  { key: "duplicate_attendance", label: "직원/날짜 중복 근태" },
  { key: "invalid_work_hours", label: "비정상 근무시간" },
  { key: "invalid_overtime_hours", label: "비정상 잔업시간" },
  { key: "attendance_before_hire_date", label: "입사 전 근태" },
  { key: "attendance_after_resignation", label: "퇴사 후 근태" },
  { key: "factory_line_mismatch", label: "공장-라인 불일치" },
];
