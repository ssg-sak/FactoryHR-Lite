const MESSAGE_MAP: Record<string, string> = {
  "Employee number already exists": "이미 사용 중인 사번입니다.",
  "Production line does not belong to the selected factory":
    "선택한 생산라인은 해당 공장에 속하지 않습니다.",
  "resigned_at must be on or after hired_at": "퇴사일은 입사일보다 빠를 수 없습니다.",
  "active employees cannot have resigned_at": "재직 직원은 퇴사일을 가질 수 없습니다.",
  "resigned employees require resigned_at": "퇴사 직원은 퇴사일이 필요합니다.",
  "Employee has attendance records and cannot be deleted":
    "근태 기록이 있는 직원은 삭제할 수 없습니다.",
  "Attendance cannot be before hired_at": "입사일 이전 날짜에는 근태를 등록할 수 없습니다.",
  "Attendance cannot be after resigned_at": "퇴사일 이후 날짜에는 근태를 등록할 수 없습니다.",
  "Attendance already exists for this employee and date":
    "해당 직원의 같은 날짜 근태가 이미 있습니다.",
  "date_from cannot be after date_to": "시작일은 종료일보다 늦을 수 없습니다.",
  "Employee not found": "직원을 찾을 수 없습니다.",
  "Department not found": "부서를 찾을 수 없습니다.",
  "Factory not found": "공장을 찾을 수 없습니다.",
  "Shift not found": "교대조를 찾을 수 없습니다.",
  "Production line not found": "생산라인을 찾을 수 없습니다.",
  "Attendance record not found": "근태 기록을 찾을 수 없습니다.",
  "Existing attendance is before the new hired_at":
    "기존 근태가 새 입사일보다 이전입니다.",
  "Existing attendance is after the new resigned_at":
    "기존 근태가 새 퇴사일보다 이후입니다.",
  "Invalid username or password": "사용자 이름 또는 비밀번호가 올바르지 않습니다.",
  "This account is inactive": "비활성화된 계정입니다.",
  "Not authenticated": "로그인이 필요합니다.",
  "Admin role required": "관리자 권한이 필요합니다.",
  "Token has expired": "로그인 시간이 만료되었습니다. 다시 로그인하세요.",
  "Could not validate credentials": "인증 정보를 확인할 수 없습니다.",
};

const FIELD_LABEL: Record<string, string> = {
  employee_number: "사번",
  name: "이름",
  department_id: "부서",
  factory_id: "공장",
  production_line_id: "생산라인",
  shift_id: "교대조",
  hired_at: "입사일",
  resigned_at: "퇴사일",
  status: "상태",
  employee_id: "직원",
  work_date: "날짜",
  work_hours: "근무시간",
  overtime_hours: "잔업시간",
  attendance_status: "근태 상태",
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

function translate(message: string): string {
  return MESSAGE_MAP[message] ?? message;
}

export function formatApiError(status: number, detail: unknown): string {
  if (typeof detail === "string") {
    return translate(detail);
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (!item || typeof item !== "object") {
          return "입력값을 확인하세요.";
        }
        const loc = Array.isArray((item as { loc?: unknown }).loc)
          ? ((item as { loc: unknown[] }).loc.filter((part) => part !== "body") as string[])
          : [];
        const field = FIELD_LABEL[String(loc[0] ?? "")] ?? loc[0];
        const msg = String((item as { msg?: string }).msg ?? "유효하지 않습니다.");
        if (msg.includes("less than or equal to 16") || msg.includes("<= 16")) {
          return "근무시간은 16시간을 넘을 수 없습니다.";
        }
        if (msg.includes("less than or equal to 8") || msg.includes("<= 8")) {
          return "잔업시간은 8시간을 넘을 수 없습니다.";
        }
        if (msg.includes("greater than or equal to 0")) {
          return field ? `${field}은(는) 0 이상이어야 합니다.` : "0 이상이어야 합니다.";
        }
        return field ? `${field}: ${translate(msg)}` : translate(msg);
      })
      .join(" ");
  }
  if (status === 401) {
    return typeof detail === "string" ? translate(detail) : "로그인이 필요합니다.";
  }
  if (status === 403) {
    return typeof detail === "string" ? translate(detail) : "이 작업을 수행할 권한이 없습니다.";
  }
  if (status === 422) {
    return "입력값을 확인하세요.";
  }
  return "요청을 처리하지 못했습니다.";
}
