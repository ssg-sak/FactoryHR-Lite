import os
from collections.abc import Generator
from datetime import date, time
from decimal import Decimal

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
if not TEST_DATABASE_URL:
    pytest.skip(
        "TEST_DATABASE_URL is required for PostgreSQL integration tests",
        allow_module_level=True,
    )
if make_url(TEST_DATABASE_URL).get_backend_name() != "postgresql":
    pytest.exit("Tests require PostgreSQL; SQLite would not verify DB triggers")
if not (make_url(TEST_DATABASE_URL).database or "").endswith("_test"):
    pytest.exit("Refusing to run: test database name must end with '_test'")

os.environ["DATABASE_URL"] = TEST_DATABASE_URL

os.environ.setdefault("JWT_SECRET", "test-only-secret-not-for-production")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")

from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Attendance,
    Department,
    Employee,
    Factory,
    ProductionLine,
    Shift,
    User,
    UserRole,
)
from app.services.password_service import hash_password  # noqa: E402

test_engine = create_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(
    bind=test_engine, autoflush=False, expire_on_commit=False
)


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Generator[None, None, None]:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(config, "head")
    yield


@pytest.fixture()
def db(migrated_database: None) -> Generator[Session, None, None]:
    with test_engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE TABLE attendance, employees, production_lines, "
                "departments, factories, shifts, users RESTART IDENTITY CASCADE"
            )
        )

    with TestSessionLocal() as session:
        prod = Department(code="PROD", name="생산")
        qa = Department(code="QA", name="품질")
        daegu = Factory(code="DAEGU", name="대구1공장")
        gumi = Factory(code="GUMI", name="구미1공장")
        day = Shift(code="DAY", name="주간조", start_time=time(8), end_time=time(17))
        night = Shift(
            code="NIGHT", name="야간조", start_time=time(20), end_time=time(5)
        )
        session.add_all([prod, qa, daegu, gumi, day, night])
        session.flush()
        daegu_line = ProductionLine(factory_id=daegu.id, code="A", name="조립 A라인")
        gumi_line = ProductionLine(factory_id=gumi.id, code="A", name="가공 A라인")
        session.add_all([daegu_line, gumi_line])
        session.flush()
        active = Employee(
            employee_number="FHR-0001",
            name="김민준",
            department_id=prod.id,
            factory_id=daegu.id,
            production_line_id=daegu_line.id,
            shift_id=day.id,
            position="사원",
            hired_at=date(2024, 1, 1),
            status="active",
        )
        no_attendance = Employee(
            employee_number="FHR-0002",
            name="이서연",
            department_id=qa.id,
            factory_id=daegu.id,
            production_line_id=None,
            shift_id=night.id,
            position="사원",
            hired_at=date(2024, 6, 1),
            status="active",
        )
        resigned = Employee(
            employee_number="FHR-0003",
            name="박도윤",
            department_id=prod.id,
            factory_id=gumi.id,
            production_line_id=gumi_line.id,
            shift_id=day.id,
            hired_at=date(2023, 1, 1),
            resigned_at=date(2026, 1, 31),
            status="resigned",
        )
        session.add_all([active, no_attendance, resigned])
        session.flush()
        session.add_all(
            [
                Attendance(
                    employee_id=active.id,
                    work_date=date(2026, 1, 10),
                    work_hours=Decimal("8"),
                    overtime_hours=Decimal("2"),
                    attendance_status="present",
                ),
                Attendance(
                    employee_id=active.id,
                    work_date=date(2026, 1, 11),
                    work_hours=Decimal("0"),
                    overtime_hours=Decimal("0"),
                    attendance_status="absent",
                ),
                Attendance(
                    employee_id=resigned.id,
                    work_date=date(2026, 1, 15),
                    work_hours=Decimal("7"),
                    overtime_hours=Decimal("1"),
                    attendance_status="late",
                ),
            ]
        )
        session.add_all(
            [
                User(
                    username="admin",
                    password_hash=hash_password("admin-test"),
                    role=UserRole.ADMIN.value,
                    is_active=True,
                ),
                User(
                    username="viewer",
                    password_hash=hash_password("viewer-demo"),
                    role=UserRole.VIEWER.value,
                    is_active=True,
                ),
                User(
                    username="inactive",
                    password_hash=hash_password("inactive-test"),
                    role=UserRole.VIEWER.value,
                    is_active=False,
                ),
            ]
        )
        session.commit()
        yield session


def _login(test_client: TestClient, username: str, password: str) -> str:
    response = test_client.post(
        "/auth/login", json={"username": username, "password": password}
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


@pytest.fixture()
def client(db: Session) -> TestClient:
    test_client = TestClient(app)
    token = _login(test_client, "admin", "admin-test")
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    return test_client


@pytest.fixture()
def viewer_client(db: Session) -> TestClient:
    test_client = TestClient(app)
    token = _login(test_client, "viewer", "viewer-demo")
    test_client.headers.update({"Authorization": f"Bearer {token}"})
    return test_client


@pytest.fixture()
def anonymous_client(db: Session) -> TestClient:
    return TestClient(app)


@pytest.fixture()
def reference_ids(db: Session) -> dict[str, int]:
    return {
        "prod": db.scalar(select(Department).where(Department.code == "PROD")).id,
        "qa": db.scalar(select(Department).where(Department.code == "QA")).id,
        "daegu": db.scalar(select(Factory).where(Factory.code == "DAEGU")).id,
        "gumi": db.scalar(select(Factory).where(Factory.code == "GUMI")).id,
        "daegu_line": db.scalar(
            select(ProductionLine).where(
                ProductionLine.factory_id == 1, ProductionLine.code == "A"
            )
        ).id,
        "gumi_line": db.scalar(
            select(ProductionLine).where(
                ProductionLine.factory_id == 2, ProductionLine.code == "A"
            )
        ).id,
        "day": db.scalar(select(Shift).where(Shift.code == "DAY")).id,
        "night": db.scalar(select(Shift).where(Shift.code == "NIGHT")).id,
    }
