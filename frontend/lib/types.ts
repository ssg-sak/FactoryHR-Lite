export type EmployeeStatus = "active" | "resigned";
export type AttendanceStatus = "present" | "late" | "absent" | "leave";

export interface Department {
  id: number;
  code: string;
  name: string;
}

export interface Factory extends Department {
  location: string | null;
}

export interface ProductionLine extends Department {
  factory_id: number;
  factory_name: string;
}

export interface Shift extends Department {
  start_time: string | null;
  end_time: string | null;
}

export interface Employee {
  id: number;
  employee_number: string;
  name: string;
  department_id: number;
  department_name: string;
  factory_id: number;
  factory_name: string;
  production_line_id: number | null;
  production_line_name: string | null;
  shift_id: number;
  shift_name: string;
  position: string | null;
  hired_at: string;
  resigned_at: string | null;
  status: EmployeeStatus;
  created_at: string;
  updated_at: string;
}

export interface EmployeeListResponse {
  items: Employee[];
  total: number;
  page: number;
  page_size: number;
}

export interface EmployeeWritePayload {
  employee_number: string;
  name: string;
  department_id: number;
  factory_id: number;
  production_line_id: number | null;
  shift_id: number;
  position: string | null;
  hired_at: string;
  resigned_at: string | null;
  status: EmployeeStatus;
}

export interface Attendance {
  id: number;
  employee_id: number;
  employee_number: string;
  employee_name: string;
  factory_name: string;
  production_line_name: string | null;
  shift_name: string;
  work_date: string;
  work_hours: number | string;
  overtime_hours: number | string;
  attendance_status: AttendanceStatus;
  created_at: string;
  updated_at: string;
}

export interface AttendanceListResponse {
  items: Attendance[];
  total: number;
  page: number;
  page_size: number;
}

export interface AttendanceWritePayload {
  employee_id: number;
  work_date: string;
  work_hours: number;
  overtime_hours: number;
  attendance_status: AttendanceStatus;
}

export interface GroupCount {
  id: number | null;
  code: string | null;
  name: string;
  count: number;
}

export interface WorkforceFilters {
  date_from?: string;
  date_to?: string;
  department_id?: number;
  factory_id?: number;
  production_line_id?: number;
  shift_id?: number;
}

export interface DashboardSummary extends WorkforceFilters {
  total_employees: number;
  active_employees: number;
  resigned_employees: number;
  resigned_in_period: number;
  average_tenure_months: number;
  absence_rate: number;
  late_rate: number;
  average_overtime_hours: number;
  attendance_records: number;
  employees_by_department: GroupCount[];
  employees_by_factory: GroupCount[];
  employees_by_line: GroupCount[];
  employees_by_shift: GroupCount[];
  metric_definitions: Record<string, string>;
}

export interface WorkforceDistribution extends WorkforceFilters {
  active_by_factory: GroupCount[];
  active_by_line: GroupCount[];
  active_by_shift: GroupCount[];
  resignations_by_department: GroupCount[];
  resignations_by_line: GroupCount[];
}

export interface AttendanceTrendPoint {
  work_date: string;
  total: number;
  present: number;
  late: number;
  absent: number;
  leave: number;
  absence_rate: number;
  late_rate: number;
}

export interface AttendanceTrend extends WorkforceFilters {
  points: AttendanceTrendPoint[];
}

export interface OvertimeGroup {
  id: number | null;
  code: string | null;
  name: string;
  average_overtime_hours: number;
  record_count: number;
}

export interface OvertimeSummary extends WorkforceFilters {
  by_production_line: OvertimeGroup[];
  by_shift: OvertimeGroup[];
}

export interface TenureBand {
  key: string;
  label: string;
  count: number;
}

export interface TenureDistribution extends WorkforceFilters {
  report_date: string;
  bands: TenureBand[];
  definition: string;
}

export interface DataQualityResult {
  total_employees: number;
  total_attendance_records: number;
  duplicate_employee_numbers: number;
  duplicate_attendance: number;
  invalid_work_hours: number;
  invalid_overtime_hours: number;
  attendance_before_hire_date: number;
  attendance_after_resignation: number;
  factory_line_mismatch: number;
}

export interface AIReportResponse {
  observations: string[];
  additional_data_needed: string[];
  cannot_conclude: string[];
}
