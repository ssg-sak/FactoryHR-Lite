from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Attendance,
    Department,
    Employee,
    EmployeeStatus,
    Factory,
    ProductionLine,
    Shift,
)
from app.schemas.employee import EmployeeCreate, EmployeeUpdate, validate_employment_dates


EMPLOYEE_LOAD_OPTIONS = (
    joinedload(Employee.department),
    joinedload(Employee.factory),
    joinedload(Employee.production_line),
    joinedload(Employee.shift),
)


def get_employee_or_404(db: Session, employee_id: int) -> Employee:
    employee = db.scalar(
        select(Employee)
        .where(Employee.id == employee_id)
        .options(*EMPLOYEE_LOAD_OPTIONS)
    )
    if employee is None:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


def employee_response(employee: Employee) -> dict[str, object]:
    return {
        "id": employee.id,
        "employee_number": employee.employee_number,
        "name": employee.name,
        "department_id": employee.department_id,
        "department_name": employee.department.name,
        "factory_id": employee.factory_id,
        "factory_name": employee.factory.name,
        "production_line_id": employee.production_line_id,
        "production_line_name": (
            employee.production_line.name if employee.production_line else None
        ),
        "shift_id": employee.shift_id,
        "shift_name": employee.shift.name,
        "position": employee.position,
        "hired_at": employee.hired_at,
        "resigned_at": employee.resigned_at,
        "status": employee.status,
        "created_at": employee.created_at,
        "updated_at": employee.updated_at,
    }


def list_employees(
    db: Session,
    *,
    page: int,
    page_size: int,
    name: str | None = None,
    department_id: int | None = None,
    factory_id: int | None = None,
    production_line_id: int | None = None,
    shift_id: int | None = None,
    employee_status: EmployeeStatus | None = None,
) -> tuple[list[Employee], int]:
    filters = []
    if name:
        filters.append(Employee.name.ilike(f"%{name.strip()}%"))
    if department_id is not None:
        filters.append(Employee.department_id == department_id)
    if factory_id is not None:
        filters.append(Employee.factory_id == factory_id)
    if production_line_id is not None:
        filters.append(Employee.production_line_id == production_line_id)
    if shift_id is not None:
        filters.append(Employee.shift_id == shift_id)
    if employee_status is not None:
        filters.append(Employee.status == employee_status.value)

    total = db.scalar(select(func.count(Employee.id)).where(*filters)) or 0
    employees = list(
        db.scalars(
            select(Employee)
            .where(*filters)
            .options(*EMPLOYEE_LOAD_OPTIONS)
            .order_by(Employee.employee_number)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
    )
    return employees, total


def validate_references(
    db: Session,
    *,
    department_id: int,
    factory_id: int,
    production_line_id: int | None,
    shift_id: int,
) -> None:
    if db.get(Department, department_id) is None:
        raise HTTPException(status_code=400, detail="Department not found")
    if db.get(Factory, factory_id) is None:
        raise HTTPException(status_code=400, detail="Factory not found")
    if db.get(Shift, shift_id) is None:
        raise HTTPException(status_code=400, detail="Shift not found")
    if production_line_id is not None:
        line = db.get(ProductionLine, production_line_id)
        if line is None:
            raise HTTPException(status_code=400, detail="Production line not found")
        if line.factory_id != factory_id:
            raise HTTPException(
                status_code=400,
                detail="Production line does not belong to the selected factory",
            )


def ensure_employee_number_available(
    db: Session, employee_number: str, exclude_id: int | None = None
) -> None:
    statement = select(Employee.id).where(Employee.employee_number == employee_number)
    if exclude_id is not None:
        statement = statement.where(Employee.id != exclude_id)
    if db.scalar(statement) is not None:
        raise HTTPException(status_code=409, detail="Employee number already exists")


def create_employee(db: Session, payload: EmployeeCreate) -> Employee:
    ensure_employee_number_available(db, payload.employee_number)
    validate_references(
        db,
        department_id=payload.department_id,
        factory_id=payload.factory_id,
        production_line_id=payload.production_line_id,
        shift_id=payload.shift_id,
    )
    employee = Employee(**payload.model_dump())
    db.add(employee)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Employee could not be created") from exc
    return get_employee_or_404(db, employee.id)


def update_employee(db: Session, employee_id: int, payload: EmployeeUpdate) -> Employee:
    employee = get_employee_or_404(db, employee_id)
    changes = payload.model_dump(exclude_unset=True)

    prospective = {
        "employee_number": changes.get("employee_number", employee.employee_number),
        "department_id": changes.get("department_id", employee.department_id),
        "factory_id": changes.get("factory_id", employee.factory_id),
        "production_line_id": changes.get(
            "production_line_id", employee.production_line_id
        ),
        "shift_id": changes.get("shift_id", employee.shift_id),
        "hired_at": changes.get("hired_at", employee.hired_at),
        "resigned_at": changes.get("resigned_at", employee.resigned_at),
        "status": EmployeeStatus(changes.get("status", employee.status)),
    }
    try:
        validate_employment_dates(
            date.fromisoformat(prospective["hired_at"])
            if isinstance(prospective["hired_at"], str)
            else prospective["hired_at"],
            date.fromisoformat(prospective["resigned_at"])
            if isinstance(prospective["resigned_at"], str)
            else prospective["resigned_at"],
            prospective["status"],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    ensure_employee_number_available(
        db, str(prospective["employee_number"]), exclude_id=employee_id
    )
    validate_references(
        db,
        department_id=int(prospective["department_id"]),
        factory_id=int(prospective["factory_id"]),
        production_line_id=prospective["production_line_id"],
        shift_id=int(prospective["shift_id"]),
    )

    first_attendance, last_attendance = db.execute(
        select(func.min(Attendance.work_date), func.max(Attendance.work_date)).where(
            Attendance.employee_id == employee_id
        )
    ).one()
    hired_at = prospective["hired_at"]
    resigned_at = prospective["resigned_at"]
    if isinstance(hired_at, str):
        hired_at = date.fromisoformat(hired_at)
    if isinstance(resigned_at, str):
        resigned_at = date.fromisoformat(resigned_at)
    if first_attendance is not None and first_attendance < hired_at:
        raise HTTPException(
            status_code=409, detail="Existing attendance is before the new hired_at"
        )
    if resigned_at is not None and last_attendance is not None and last_attendance > resigned_at:
        raise HTTPException(
            status_code=409, detail="Existing attendance is after the new resigned_at"
        )

    for field, value in changes.items():
        setattr(employee, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Employee could not be updated") from exc
    return get_employee_or_404(db, employee_id)


def delete_employee(db: Session, employee_id: int) -> None:
    employee = get_employee_or_404(db, employee_id)
    has_attendance = db.scalar(
        select(Attendance.id).where(Attendance.employee_id == employee_id).limit(1)
    )
    if has_attendance is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee has attendance records and cannot be deleted",
        )
    db.delete(employee)
    db.commit()
