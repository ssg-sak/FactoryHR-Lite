import random
from datetime import date, time, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models import (
    Attendance,
    AttendanceStatus,
    Department,
    Employee,
    EmployeeStatus,
    Factory,
    ProductionLine,
    Shift,
)
from app.services.user_bootstrap import bootstrap_managed_accounts

RANDOM_SEED = 20260828
ATTENDANCE_END_DATE = date(2026, 8, 27)

DEPARTMENT_DATA = [
    ("PROD", "생산"),
    ("QA", "품질"),
    ("MAINT", "설비"),
    ("ADMIN", "관리"),
]
FACTORY_DATA = [
    ("DAEGU", "대구1공장", "대구광역시 달성군"),
    ("GUMI", "구미1공장", "경상북도 구미시"),
]
LINE_DATA = {
    "DAEGU": [("A", "조립 A라인"), ("B", "조립 B라인"), ("PACK", "포장라인")],
    "GUMI": [("A", "가공 A라인"), ("B", "가공 B라인"), ("PACK", "포장라인")],
}
NAMES = [
    "김민준", "이서준", "박도윤", "최예준", "정시우", "강지호", "조하준", "윤도현",
    "장우진", "임건우", "한유준", "오현우", "서지훈", "신준호", "권민재", "황은우",
    "안서진", "송지후", "전수현", "홍재윤", "김서연", "이하은", "박지민", "최수아",
    "정유나", "강예은", "조채원", "윤다은", "장소윤", "임지아", "한예린", "오하윤",
    "서유진", "신채윤", "권서아", "황지안", "안나연", "송예나", "전다인", "홍수빈",
    "김태윤", "이현준", "박시온", "최도현", "정우빈", "강민재", "조현서", "윤지후",
    "장준영", "임성민",
]


def seed_reference_data(
    session: Session,
) -> tuple[
    dict[str, Department],
    dict[str, Factory],
    dict[str, ProductionLine],
    dict[str, Shift],
]:
    departments = {
        code: Department(code=code, name=name) for code, name in DEPARTMENT_DATA
    }
    factories = {
        code: Factory(code=code, name=name, location=location)
        for code, name, location in FACTORY_DATA
    }
    shifts = {
        "DAY": Shift(
            code="DAY", name="주간조", start_time=time(8), end_time=time(17)
        ),
        "NIGHT": Shift(
            code="NIGHT", name="야간조", start_time=time(20), end_time=time(5)
        ),
    }
    session.add_all([*departments.values(), *factories.values(), *shifts.values()])
    session.flush()

    lines: dict[str, ProductionLine] = {}
    for factory_code, line_items in LINE_DATA.items():
        for line_code, line_name in line_items:
            key = f"{factory_code}-{line_code}"
            lines[key] = ProductionLine(
                factory_id=factories[factory_code].id,
                code=line_code,
                name=line_name,
            )
    session.add_all(lines.values())
    session.flush()
    return departments, factories, lines, shifts


def seed_employees(
    session: Session,
    departments: dict[str, Department],
    factories: dict[str, Factory],
    lines: dict[str, ProductionLine],
    shifts: dict[str, Shift],
) -> list[Employee]:
    rng = random.Random(RANDOM_SEED)
    department_codes = ["PROD"] * 34 + ["QA"] * 6 + ["MAINT"] * 5 + ["ADMIN"] * 5
    resignation_dates = {
        8: date(2026, 8, 8),
        23: date(2026, 8, 14),
        39: date(2026, 8, 20),
        47: date(2026, 8, 25),
    }
    employees: list[Employee] = []

    for index, (name, department_code) in enumerate(zip(NAMES, department_codes), start=1):
        factory_code = "DAEGU" if index <= 26 else "GUMI"
        shift_code = (
            "NIGHT" if department_code == "PROD" and index % 5 == 0 else "DAY"
        )
        line: ProductionLine | None = None
        if department_code == "PROD":
            line_code = ("A", "B", "PACK")[(index - 1) % 3]
            line = lines[f"{factory_code}-{line_code}"]

        resigned_at = resignation_dates.get(index)
        hired_year = rng.choice([2022, 2023, 2024, 2025])
        hired_month = rng.randint(1, 12)
        hired_day = rng.randint(1, 28)
        employees.append(
            Employee(
                employee_number=f"FHR-{index:04d}",
                name=name,
                department_id=departments[department_code].id,
                factory_id=factories[factory_code].id,
                production_line_id=line.id if line else None,
                shift_id=shifts[shift_code].id,
                position=(
                    "반장"
                    if department_code == "PROD" and index in {1, 18, 27}
                    else "사원"
                ),
                hired_at=date(hired_year, hired_month, hired_day),
                resigned_at=resigned_at,
                status=(
                    EmployeeStatus.RESIGNED.value
                    if resigned_at
                    else EmployeeStatus.ACTIVE.value
                ),
            )
        )

    session.add_all(employees)
    session.flush()
    return employees


def seed_attendance(session: Session, employees: list[Employee]) -> int:
    rng = random.Random(RANDOM_SEED)
    start_date = ATTENDANCE_END_DATE - timedelta(days=29)
    records: list[Attendance] = []

    for day_offset in range(30):
        work_date = start_date + timedelta(days=day_offset)
        if work_date.weekday() >= 5:
            continue
        for employee in employees:
            if work_date < employee.hired_at:
                continue
            if employee.resigned_at and work_date > employee.resigned_at:
                continue

            roll = rng.random()
            if roll < 0.03:
                status, work_hours = AttendanceStatus.ABSENT.value, Decimal("0")
            elif roll < 0.08:
                status, work_hours = AttendanceStatus.LEAVE.value, Decimal("0")
            elif roll < 0.16:
                status, work_hours = AttendanceStatus.LATE.value, Decimal("7")
            else:
                status, work_hours = AttendanceStatus.PRESENT.value, Decimal("8")

            overtime_hours = Decimal("0")
            if (
                employee.production_line_id is not None
                and status in {AttendanceStatus.PRESENT.value, AttendanceStatus.LATE.value}
                and rng.random() < 0.28
            ):
                overtime_hours = rng.choice([Decimal("1"), Decimal("2"), Decimal("3")])

            records.append(
                Attendance(
                    employee_id=employee.id,
                    work_date=work_date,
                    work_hours=work_hours,
                    overtime_hours=overtime_hours,
                    attendance_status=status,
                )
            )

    session.add_all(records)
    session.flush()
    return len(records)


def run_seed() -> None:
    with SessionLocal() as session:
        accounts = bootstrap_managed_accounts(session)
        session.commit()
        if accounts:
            print("Managed accounts upserted: " + ", ".join(accounts))

        existing_employees = session.scalar(select(func.count(Employee.id))) or 0
        if existing_employees:
            print(f"Seed skipped: employees table already has {existing_employees} rows.")
            return
        try:
            departments, factories, lines, shifts = seed_reference_data(session)
            employees = seed_employees(session, departments, factories, lines, shifts)
            attendance_count = seed_attendance(session, employees)
            session.commit()
        except Exception:
            session.rollback()
            raise

        print(
            "Seed complete: "
            f"{len(departments)} departments, {len(factories)} factories, "
            f"{len(lines)} production lines, {len(shifts)} shifts, "
            f"{len(employees)} employees, {attendance_count} attendance records."
        )


if __name__ == "__main__":
    run_seed()

