"""Workforce and attendance metrics with explicit definitions.

Days-per-month divisor: 30.4375 (365.25 / 12).

Absence record rate
    = absent attendance rows / attendance rows in the selected period * 100

Late record rate
    = late attendance rows / attendance rows in the selected period * 100

Average overtime hours
    = mean(overtime_hours) of attendance rows in the selected period

Average tenure months
    active: (report_date - hired_at) / 30.4375
    resigned: (resigned_at - hired_at) / 30.4375
    report_date is date_to when provided, otherwise CURRENT_DATE

Resigned in period
    = employees with status=resigned whose resigned_at falls in [date_from, date_to]
    Missing bound is treated as unbounded on that side.

Headcount charts in workforce-distribution count status=active only.
Summary employees_by_* counts keep the original all-employee grouping.
"""

from datetime import date

from fastapi import HTTPException
from sqlalchemy import and_, case, func, literal, select
from sqlalchemy.orm import Session
from sqlalchemy.sql.elements import ColumnElement

from app.models import (
    Attendance,
    Department,
    Employee,
    Factory,
    ProductionLine,
    Shift,
)
from app.services.filters import WorkforceFilters

DAYS_PER_MONTH = 30.4375

METRIC_DEFINITIONS = {
    "active_employees": "status=active 인 직원 수 (현재 재직)",
    "resigned_in_period": (
        "status=resigned 이고 resigned_at이 선택 기간에 포함된 직원 수"
    ),
    "average_tenure_months": (
        "근속일수 / 30.4375. 재직: report date - hired_at, "
        "퇴사: resigned_at - hired_at. report date는 date_to 또는 CURRENT_DATE"
    ),
    "average_overtime_hours": "선택 기간 attendance.overtime_hours 평균",
    "absence_rate": "선택 기간 attendance 중 attendance_status=absent 비율(%)",
    "late_rate": "선택 기간 attendance 중 attendance_status=late 비율(%)",
}


def _group_counts(
    db: Session,
    model: type,
    foreign_key: object,
    employee_clauses: list[ColumnElement[bool]] | None = None,
    extra_employee_clauses: list[ColumnElement[bool]] | None = None,
) -> list[dict[str, object]]:
    join_condition: ColumnElement[bool] = foreign_key == model.id
    extra: list[ColumnElement[bool]] = []
    if employee_clauses:
        extra.extend(employee_clauses)
    if extra_employee_clauses:
        extra.extend(extra_employee_clauses)
    if extra:
        join_condition = and_(join_condition, *extra)
    rows = db.execute(
        select(model.id, model.code, model.name, func.count(Employee.id))
        .select_from(model)
        .outerjoin(Employee, join_condition)
        .group_by(model.id, model.code, model.name)
        .order_by(model.code)
    ).all()
    return [
        {"id": row[0], "code": row[1], "name": row[2], "count": row[3]}
        for row in rows
    ]


def _safe_rate(numerator: int, denominator: int) -> float:
    if not denominator:
        return 0.0
    return round(numerator / denominator * 100, 2)


def _safe_avg(value: object, digits: int = 2) -> float:
    if value is None:
        return 0.0
    return round(float(value), digits)


def _tenure_end_expr(filters: WorkforceFilters):
    if filters.date_to is not None:
        return func.coalesce(Employee.resigned_at, literal(filters.date_to))
    return func.coalesce(Employee.resigned_at, func.current_date())


def get_dashboard_summary(
    db: Session,
    date_from: date | None = None,
    date_to: date | None = None,
    department_id: int | None = None,
    factory_id: int | None = None,
    production_line_id: int | None = None,
    shift_id: int | None = None,
    filters: WorkforceFilters | None = None,
) -> dict[str, object]:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from cannot be after date_to")

    applied = filters or WorkforceFilters(
        date_from=date_from,
        date_to=date_to,
        department_id=department_id,
        factory_id=factory_id,
        production_line_id=production_line_id,
        shift_id=shift_id,
    )
    applied.validate()
    employee_clauses = applied.employee_clauses()

    total_employees, active_employees, resigned_employees, tenure_days = db.execute(
        select(
            func.count(Employee.id),
            func.count(Employee.id).filter(Employee.status == "active"),
            func.count(Employee.id).filter(Employee.status == "resigned"),
            func.avg(_tenure_end_expr(applied) - Employee.hired_at),
        ).where(*employee_clauses)
    ).one()

    resigned_in_period = db.scalar(
        select(func.count(Employee.id)).where(
            Employee.status == "resigned",
            *employee_clauses,
            *applied.resignation_date_clauses(),
        )
    ) or 0

    attendance_stmt = select(
        func.count(Attendance.id),
        func.sum(case((Attendance.attendance_status == "absent", 1), else_=0)),
        func.sum(case((Attendance.attendance_status == "late", 1), else_=0)),
        func.avg(Attendance.overtime_hours),
    )
    if employee_clauses:
        attendance_stmt = attendance_stmt.join(
            Employee, Attendance.employee_id == Employee.id
        ).where(*employee_clauses)
    attendance_stmt = attendance_stmt.where(*applied.attendance_date_clauses())
    attendance_total, absent_count, late_count, average_overtime = db.execute(
        attendance_stmt
    ).one()

    attendance_total = attendance_total or 0
    absent_count = int(absent_count or 0)
    late_count = int(late_count or 0)
    return {
        **applied.as_dict(),
        "total_employees": total_employees or 0,
        "active_employees": active_employees or 0,
        "resigned_employees": resigned_employees or 0,
        "resigned_in_period": resigned_in_period,
        "average_tenure_months": round(float(tenure_days or 0) / DAYS_PER_MONTH, 1),
        "absence_rate": _safe_rate(absent_count, attendance_total),
        "late_rate": _safe_rate(late_count, attendance_total),
        "average_overtime_hours": _safe_avg(average_overtime),
        "attendance_records": attendance_total,
        "employees_by_department": _group_counts(
            db, Department, Employee.department_id, employee_clauses
        ),
        "employees_by_factory": _group_counts(
            db, Factory, Employee.factory_id, employee_clauses
        ),
        "employees_by_line": _group_counts(
            db, ProductionLine, Employee.production_line_id, employee_clauses
        ),
        "employees_by_shift": _group_counts(
            db, Shift, Employee.shift_id, employee_clauses
        ),
        "metric_definitions": METRIC_DEFINITIONS,
    }


def get_workforce_distribution(
    db: Session, filters: WorkforceFilters
) -> dict[str, object]:
    filters.validate()
    employee_clauses = filters.employee_clauses()
    active_clauses = [Employee.status == "active", *employee_clauses]
    return {
        **filters.as_dict(),
        "active_by_factory": _group_counts(
            db, Factory, Employee.factory_id, extra_employee_clauses=active_clauses
        ),
        "active_by_line": _group_counts(
            db,
            ProductionLine,
            Employee.production_line_id,
            extra_employee_clauses=active_clauses,
        ),
        "active_by_shift": _group_counts(
            db, Shift, Employee.shift_id, extra_employee_clauses=active_clauses
        ),
        "resignations_by_department": _group_counts(
            db,
            Department,
            Employee.department_id,
            extra_employee_clauses=[
                Employee.status == "resigned",
                *employee_clauses,
                *filters.resignation_date_clauses(),
            ],
        ),
        "resignations_by_line": _group_counts(
            db,
            ProductionLine,
            Employee.production_line_id,
            extra_employee_clauses=[
                Employee.status == "resigned",
                *employee_clauses,
                *filters.resignation_date_clauses(),
            ],
        ),
    }


def get_attendance_trend(
    db: Session, filters: WorkforceFilters
) -> dict[str, object]:
    filters.validate()
    employee_clauses = filters.employee_clauses()
    stmt = (
        select(
            Attendance.work_date,
            func.count(Attendance.id),
            func.sum(case((Attendance.attendance_status == "present", 1), else_=0)),
            func.sum(case((Attendance.attendance_status == "late", 1), else_=0)),
            func.sum(case((Attendance.attendance_status == "absent", 1), else_=0)),
            func.sum(case((Attendance.attendance_status == "leave", 1), else_=0)),
        )
        .select_from(Attendance)
    )
    if employee_clauses:
        stmt = stmt.join(Employee, Attendance.employee_id == Employee.id).where(
            *employee_clauses
        )
    stmt = (
        stmt.where(*filters.attendance_date_clauses())
        .group_by(Attendance.work_date)
        .order_by(Attendance.work_date)
    )
    points = []
    for row in db.execute(stmt):
        work_date, total, present, late, absent, leave = row
        total = total or 0
        present = int(present or 0)
        late = int(late or 0)
        absent = int(absent or 0)
        leave = int(leave or 0)
        points.append(
            {
                "work_date": work_date,
                "total": total,
                "present": present,
                "late": late,
                "absent": absent,
                "leave": leave,
                "absence_rate": _safe_rate(absent, total),
                "late_rate": _safe_rate(late, total),
            }
        )
    return {**filters.as_dict(), "points": points}


def _overtime_groups(
    db: Session,
    model: type,
    foreign_key: object,
    filters: WorkforceFilters,
) -> list[dict[str, object]]:
    employee_clauses = filters.employee_clauses()
    stmt = (
        select(
            model.id,
            model.code,
            model.name,
            func.avg(Attendance.overtime_hours),
            func.count(Attendance.id),
        )
        .select_from(Attendance)
        .join(Employee, Attendance.employee_id == Employee.id)
        .outerjoin(model, foreign_key == model.id)
        .where(*employee_clauses, *filters.attendance_date_clauses())
        .group_by(model.id, model.code, model.name)
        .order_by(model.code)
    )
    rows = []
    for row in db.execute(stmt):
        rows.append(
            {
                "id": row[0],
                "code": row[1],
                "name": row[2] or "미지정",
                "average_overtime_hours": _safe_avg(row[3]),
                "record_count": row[4] or 0,
            }
        )
    return rows


def get_overtime_summary(
    db: Session, filters: WorkforceFilters
) -> dict[str, object]:
    filters.validate()
    return {
        **filters.as_dict(),
        "by_production_line": _overtime_groups(
            db, ProductionLine, Employee.production_line_id, filters
        ),
        "by_shift": _overtime_groups(db, Shift, Employee.shift_id, filters),
    }


TENURE_BANDS = (
    ("0_6", "0~6개월", 0, 6),
    ("6_12", "6~12개월", 6, 12),
    ("12_36", "1~3년", 12, 36),
    ("36_plus", "3년 이상", 36, None),
)


def get_tenure_distribution(
    db: Session, filters: WorkforceFilters
) -> dict[str, object]:
    """Active employees only. Tenure = (report_date - hired_at) / 30.4375."""
    filters.validate()
    report_date = filters.date_to or date.today()
    employee_clauses = [
        Employee.status == "active",
        *filters.employee_clauses(),
    ]
    counts = {key: 0 for key, _label, _lo, _hi in TENURE_BANDS}
    rows = db.execute(select(Employee.hired_at).where(*employee_clauses)).all()
    for (hired_at,) in rows:
        months = (report_date - hired_at).days / DAYS_PER_MONTH
        if months < 6:
            counts["0_6"] += 1
        elif months < 12:
            counts["6_12"] += 1
        elif months < 36:
            counts["12_36"] += 1
        else:
            counts["36_plus"] += 1
    bands = [
        {"key": key, "label": label, "count": counts[key]}
        for key, label, _lo, _hi in TENURE_BANDS
    ]
    return {
        **filters.as_dict(),
        "report_date": report_date,
        "bands": bands,
        "definition": (
            "재직 직원만 포함. 근속개월 = (report_date - hired_at) / 30.4375. "
            "report_date는 date_to 또는 오늘."
        ),
    }
