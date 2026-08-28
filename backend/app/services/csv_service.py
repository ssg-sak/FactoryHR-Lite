import csv
import io
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Attendance, Employee
from app.services.filters import WorkforceFilters


def _utf8_bom_csv(rows: list[list[object]]) -> bytes:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerows(rows)
    return ("\ufeff" + buffer.getvalue()).encode("utf-8")


def employees_csv(db: Session, filters: WorkforceFilters) -> bytes:
    filters.validate()
    statement = (
        select(Employee)
        .options(
            selectinload(Employee.department),
            selectinload(Employee.factory),
            selectinload(Employee.production_line),
            selectinload(Employee.shift),
        )
        .where(*filters.employee_clauses())
        .order_by(Employee.employee_number)
    )
    header = [
        "employee_number",
        "name",
        "department",
        "factory",
        "production_line",
        "shift",
        "position",
        "hired_at",
        "resigned_at",
        "status",
    ]
    rows: list[list[object]] = [header]
    for employee in db.scalars(statement):
        rows.append(
            [
                employee.employee_number,
                employee.name,
                employee.department.name,
                employee.factory.name,
                employee.production_line.name if employee.production_line else "",
                employee.shift.name,
                employee.position or "",
                employee.hired_at.isoformat(),
                employee.resigned_at.isoformat() if employee.resigned_at else "",
                employee.status,
            ]
        )
    return _utf8_bom_csv(rows)


def attendance_csv(db: Session, filters: WorkforceFilters) -> bytes:
    filters.validate()
    statement = (
        select(Attendance)
        .join(Employee, Attendance.employee_id == Employee.id)
        .options(
            selectinload(Attendance.employee).selectinload(Employee.factory),
            selectinload(Attendance.employee).selectinload(Employee.production_line),
            selectinload(Attendance.employee).selectinload(Employee.shift),
        )
        .where(*filters.employee_clauses(), *filters.attendance_date_clauses())
        .order_by(Attendance.work_date, Employee.employee_number)
    )
    header = [
        "work_date",
        "employee_number",
        "employee_name",
        "factory",
        "production_line",
        "shift",
        "attendance_status",
        "work_hours",
        "overtime_hours",
    ]
    rows: list[list[object]] = [header]
    for record in db.scalars(statement):
        employee = record.employee
        rows.append(
            [
                record.work_date.isoformat(),
                employee.employee_number,
                employee.name,
                employee.factory.name,
                employee.production_line.name if employee.production_line else "",
                employee.shift.name,
                record.attendance_status,
                str(record.work_hours),
                str(record.overtime_hours),
            ]
        )
    return _utf8_bom_csv(rows)


def report_filename_stamp(value: date | None = None) -> str:
    return (value or date.today()).strftime("%Y%m%d")
