from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.attendance import AttendanceStatus


class AttendanceBase(BaseModel):
    employee_id: int = Field(gt=0)
    work_date: date
    work_hours: Decimal = Field(default=Decimal("0"), ge=0, le=16)
    overtime_hours: Decimal = Field(default=Decimal("0"), ge=0, le=8)
    attendance_status: AttendanceStatus


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    employee_id: int | None = Field(default=None, gt=0)
    work_date: date | None = None
    work_hours: Decimal | None = Field(default=None, ge=0, le=16)
    overtime_hours: Decimal | None = Field(default=None, ge=0, le=8)
    attendance_status: AttendanceStatus | None = None


class AttendanceResponse(AttendanceBase):
    id: int
    employee_number: str
    employee_name: str
    factory_name: str
    production_line_name: str | None
    shift_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AttendanceListResponse(BaseModel):
    items: list[AttendanceResponse]
    total: int
    page: int
    page_size: int

