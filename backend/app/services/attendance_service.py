from datetime import date

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Attendance, AttendanceStatus, Employee
from app.schemas.attendance import AttendanceCreate, AttendanceUpdate


def _attendance_load_options():
    return (
        selectinload(Attendance.employee).selectinload(Employee.factory),
        selectinload(Attendance.employee).selectinload(Employee.production_line),
        selectinload(Attendance.employee).selectinload(Employee.shift),
    )


def get_attendance_or_404(db: Session, attendance_id: int) -> Attendance:
    record = db.scalar(
        select(Attendance)
        .where(Attendance.id == attendance_id)
        .options(*_attendance_load_options())
    )
    if record is None:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    return record


def attendance_response(record: Attendance) -> dict[str, object]:
    return {
        "id": record.id,
        "employee_id": record.employee_id,
        "employee_number": record.employee.employee_number,
        "employee_name": record.employee.name,
        "factory_name": record.employee.factory.name,
        "production_line_name": (
            record.employee.production_line.name
            if record.employee.production_line
            else None
        ),
        "shift_name": record.employee.shift.name,
        "work_date": record.work_date,
        "work_hours": record.work_hours,
        "overtime_hours": record.overtime_hours,
        "attendance_status": record.attendance_status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def list_attendance(
    db: Session,
    *,
    page: int,
    page_size: int,
    employee_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    attendance_status: AttendanceStatus | None = None,
) -> tuple[list[Attendance], int]:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from cannot be after date_to")
    filters = []
    if employee_id is not None:
        filters.append(Attendance.employee_id == employee_id)
    if date_from is not None:
        filters.append(Attendance.work_date >= date_from)
    if date_to is not None:
        filters.append(Attendance.work_date <= date_to)
    if attendance_status is not None:
        filters.append(Attendance.attendance_status == attendance_status.value)

    total = db.scalar(select(func.count(Attendance.id)).where(*filters)) or 0
    records = list(
        db.scalars(
            select(Attendance)
            .where(*filters)
            .options(*_attendance_load_options())
            .order_by(Attendance.work_date.desc(), Attendance.employee_id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return records, total


def validate_attendance_date(employee: Employee, work_date: date) -> None:
    if work_date < employee.hired_at:
        raise HTTPException(status_code=400, detail="Attendance cannot be before hired_at")
    if employee.resigned_at is not None and work_date > employee.resigned_at:
        raise HTTPException(status_code=400, detail="Attendance cannot be after resigned_at")


def ensure_attendance_unique(
    db: Session, employee_id: int, work_date: date, exclude_id: int | None = None
) -> None:
    statement = select(Attendance.id).where(
        Attendance.employee_id == employee_id,
        Attendance.work_date == work_date,
    )
    if exclude_id is not None:
        statement = statement.where(Attendance.id != exclude_id)
    if db.scalar(statement) is not None:
        raise HTTPException(
            status_code=409,
            detail="Attendance already exists for this employee and date",
        )


def create_attendance(db: Session, payload: AttendanceCreate) -> Attendance:
    employee = db.get(Employee, payload.employee_id)
    if employee is None:
        raise HTTPException(status_code=400, detail="Employee not found")
    validate_attendance_date(employee, payload.work_date)
    ensure_attendance_unique(db, payload.employee_id, payload.work_date)
    record = Attendance(**payload.model_dump())
    db.add(record)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Attendance could not be created") from exc
    return get_attendance_or_404(db, record.id)


def update_attendance(
    db: Session, attendance_id: int, payload: AttendanceUpdate
) -> Attendance:
    record = get_attendance_or_404(db, attendance_id)
    changes = payload.model_dump(exclude_unset=True)
    employee_id = int(changes.get("employee_id", record.employee_id))
    work_date = changes.get("work_date", record.work_date)
    if isinstance(work_date, str):
        work_date = date.fromisoformat(work_date)
    employee = db.get(Employee, employee_id)
    if employee is None:
        raise HTTPException(status_code=400, detail="Employee not found")
    validate_attendance_date(employee, work_date)
    ensure_attendance_unique(db, employee_id, work_date, exclude_id=attendance_id)
    for field, value in changes.items():
        setattr(record, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Attendance could not be updated") from exc
    return get_attendance_or_404(db, attendance_id)


def delete_attendance(db: Session, attendance_id: int) -> None:
    record = get_attendance_or_404(db, attendance_id)
    db.delete(record)
    db.commit()
