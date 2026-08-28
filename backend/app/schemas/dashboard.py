from datetime import date

from pydantic import BaseModel, Field


class GroupCount(BaseModel):
    id: int | None
    code: str | None
    name: str
    count: int


class OvertimeGroup(BaseModel):
    id: int | None
    code: str | None
    name: str
    average_overtime_hours: float
    record_count: int


class AttendanceTrendPoint(BaseModel):
    work_date: date
    total: int
    present: int
    late: int
    absent: int
    leave: int
    absence_rate: float
    late_rate: float


class TenureBand(BaseModel):
    key: str
    label: str
    count: int


class FilterFields(BaseModel):
    date_from: date | None = None
    date_to: date | None = None
    department_id: int | None = None
    factory_id: int | None = None
    production_line_id: int | None = None
    shift_id: int | None = None


class DashboardSummaryResponse(FilterFields):
    total_employees: int
    active_employees: int
    resigned_employees: int
    resigned_in_period: int
    average_tenure_months: float
    absence_rate: float
    late_rate: float
    average_overtime_hours: float
    attendance_records: int
    employees_by_department: list[GroupCount]
    employees_by_factory: list[GroupCount]
    employees_by_line: list[GroupCount]
    employees_by_shift: list[GroupCount]
    metric_definitions: dict[str, str]


class WorkforceDistributionResponse(FilterFields):
    active_by_factory: list[GroupCount]
    active_by_line: list[GroupCount]
    active_by_shift: list[GroupCount]
    resignations_by_department: list[GroupCount]
    resignations_by_line: list[GroupCount]


class AttendanceTrendResponse(FilterFields):
    points: list[AttendanceTrendPoint]


class OvertimeSummaryResponse(FilterFields):
    by_production_line: list[OvertimeGroup]
    by_shift: list[OvertimeGroup]


class TenureDistributionResponse(FilterFields):
    report_date: date
    bands: list[TenureBand]
    definition: str


class DataQualityResponse(BaseModel):
    total_employees: int
    total_attendance_records: int
    duplicate_employee_numbers: int
    duplicate_attendance: int
    invalid_work_hours: int
    invalid_overtime_hours: int
    attendance_before_hire_date: int
    attendance_after_resignation: int
    factory_line_mismatch: int


class AISummaryResponse(BaseModel):
    observations: list[str] = Field(default_factory=list)
    additional_data_needed: list[str] = Field(default_factory=list)
    cannot_conclude: list[str] = Field(default_factory=list)
