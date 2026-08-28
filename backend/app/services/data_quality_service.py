"""Integrity checks against the live database.

Constraint-backed checks are expected to return 0. They are still queried so
the UI can show the actual result rather than an assumed score.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Attendance, Employee, ProductionLine


def _duplicate_group_count(db: Session, statement) -> int:
    return len(list(db.execute(statement)))


def get_data_quality(db: Session) -> dict[str, int]:
    total_employees = db.scalar(select(func.count(Employee.id))) or 0
    total_attendance = db.scalar(select(func.count(Attendance.id))) or 0

    duplicate_employee_numbers = _duplicate_group_count(
        db,
        select(Employee.employee_number)
        .group_by(Employee.employee_number)
        .having(func.count(Employee.id) > 1),
    )
    duplicate_attendance = _duplicate_group_count(
        db,
        select(Attendance.employee_id, Attendance.work_date)
        .group_by(Attendance.employee_id, Attendance.work_date)
        .having(func.count(Attendance.id) > 1),
    )

    invalid_work_hours = db.scalar(
        select(func.count(Attendance.id)).where(
            (Attendance.work_hours < 0) | (Attendance.work_hours > 16)
        )
    ) or 0
    invalid_overtime_hours = db.scalar(
        select(func.count(Attendance.id)).where(
            (Attendance.overtime_hours < 0) | (Attendance.overtime_hours > 8)
        )
    ) or 0

    attendance_before_hire = db.scalar(
        select(func.count(Attendance.id))
        .join(Employee, Attendance.employee_id == Employee.id)
        .where(Attendance.work_date < Employee.hired_at)
    ) or 0
    attendance_after_resignation = db.scalar(
        select(func.count(Attendance.id))
        .join(Employee, Attendance.employee_id == Employee.id)
        .where(
            Employee.resigned_at.is_not(None),
            Attendance.work_date > Employee.resigned_at,
        )
    ) or 0

    factory_line_mismatch = db.scalar(
        select(func.count(Employee.id))
        .join(ProductionLine, Employee.production_line_id == ProductionLine.id)
        .where(Employee.factory_id != ProductionLine.factory_id)
    ) or 0

    return {
        "total_employees": total_employees,
        "total_attendance_records": total_attendance,
        "duplicate_employee_numbers": duplicate_employee_numbers,
        "duplicate_attendance": duplicate_attendance,
        "invalid_work_hours": invalid_work_hours,
        "invalid_overtime_hours": invalid_overtime_hours,
        "attendance_before_hire_date": attendance_before_hire,
        "attendance_after_resignation": attendance_after_resignation,
        "factory_line_mismatch": factory_line_mismatch,
    }
