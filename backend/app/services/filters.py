from dataclasses import dataclass
from datetime import date

from fastapi import HTTPException
from sqlalchemy.sql.elements import ColumnElement

from app.models import Attendance, Employee


@dataclass(frozen=True)
class WorkforceFilters:
    date_from: date | None = None
    date_to: date | None = None
    department_id: int | None = None
    factory_id: int | None = None
    production_line_id: int | None = None
    shift_id: int | None = None

    def validate(self) -> None:
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise HTTPException(status_code=400, detail="date_from cannot be after date_to")

    def as_dict(self) -> dict[str, date | int | None]:
        return {
            "date_from": self.date_from,
            "date_to": self.date_to,
            "department_id": self.department_id,
            "factory_id": self.factory_id,
            "production_line_id": self.production_line_id,
            "shift_id": self.shift_id,
        }

    def employee_clauses(self) -> list[ColumnElement[bool]]:
        clauses: list[ColumnElement[bool]] = []
        if self.department_id is not None:
            clauses.append(Employee.department_id == self.department_id)
        if self.factory_id is not None:
            clauses.append(Employee.factory_id == self.factory_id)
        if self.production_line_id is not None:
            clauses.append(Employee.production_line_id == self.production_line_id)
        if self.shift_id is not None:
            clauses.append(Employee.shift_id == self.shift_id)
        return clauses

    def attendance_date_clauses(self) -> list[ColumnElement[bool]]:
        clauses: list[ColumnElement[bool]] = []
        if self.date_from is not None:
            clauses.append(Attendance.work_date >= self.date_from)
        if self.date_to is not None:
            clauses.append(Attendance.work_date <= self.date_to)
        return clauses

    def resignation_date_clauses(self) -> list[ColumnElement[bool]]:
        clauses: list[ColumnElement[bool]] = []
        if self.date_from is not None:
            clauses.append(Employee.resigned_at >= self.date_from)
        if self.date_to is not None:
            clauses.append(Employee.resigned_at <= self.date_to)
        return clauses
