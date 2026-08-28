from datetime import UTC, datetime, timedelta

import jwt
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.user import User
from app.services.auth_service import INVALID_CREDENTIALS
from app.services.password_service import verify_password


def test_password_is_hashed_not_plaintext(db: Session) -> None:
    user = db.scalar(select(User).where(User.username == "admin"))
    assert user is not None
    assert user.password_hash != "admin-test"
    assert verify_password("admin-test", user.password_hash)
    assert not verify_password("wrong-password", user.password_hash)


def test_login_success(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(
        "/auth/login", json={"username": "admin", "password": "admin-test"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["user"] == {"username": "admin", "role": "admin"}
    assert body["access_token"]


def test_login_wrong_password(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(
        "/auth/login", json={"username": "admin", "password": "nope"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS


def test_login_unknown_user(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(
        "/auth/login", json={"username": "nobody", "password": "admin-test"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == INVALID_CREDENTIALS


def test_login_inactive_user(anonymous_client: TestClient) -> None:
    response = anonymous_client.post(
        "/auth/login", json={"username": "inactive", "password": "inactive-test"}
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "This account is inactive"


def test_me_requires_auth(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/auth/me")
    assert response.status_code == 401


def test_me_with_token(client: TestClient) -> None:
    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json() == {"username": "admin", "role": "admin"}


def test_invalid_jwt(anonymous_client: TestClient) -> None:
    response = anonymous_client.get(
        "/auth/me", headers={"Authorization": "Bearer not-a-token"}
    )
    assert response.status_code == 401


def test_expired_jwt(anonymous_client: TestClient) -> None:
    token = jwt.encode(
        {
            "sub": "admin",
            "role": "admin",
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    response = anonymous_client.get(
        "/auth/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Token has expired"


def test_health_is_public(anonymous_client: TestClient) -> None:
    response = anonymous_client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_viewer_can_read(viewer_client: TestClient) -> None:
    assert viewer_client.get("/api/employees").status_code == 200
    assert viewer_client.get("/api/attendance").status_code == 200
    assert viewer_client.get("/api/dashboard/summary").status_code == 200
    assert viewer_client.get("/api/departments").status_code == 200
    assert viewer_client.get("/api/reports/employees.csv").status_code == 200


def test_viewer_cannot_write_employees(
    viewer_client: TestClient, reference_ids: dict[str, int]
) -> None:
    create = viewer_client.post(
        "/api/employees",
        json={
            "employee_number": "FHR-0099",
            "name": "테스트",
            "department_id": reference_ids["prod"],
            "factory_id": reference_ids["daegu"],
            "production_line_id": reference_ids["daegu_line"],
            "shift_id": reference_ids["day"],
            "hired_at": "2025-01-01",
            "status": "active",
        },
    )
    assert create.status_code == 403
    assert viewer_client.patch("/api/employees/1", json={"position": "x"}).status_code == 403
    assert viewer_client.delete("/api/employees/2").status_code == 403


def test_viewer_cannot_write_attendance(
    viewer_client: TestClient, reference_ids: dict[str, int]
) -> None:
    create = viewer_client.post(
        "/api/attendance",
        json={
            "employee_id": 2,
            "work_date": "2026-01-20",
            "work_hours": "8",
            "overtime_hours": "0",
            "attendance_status": "present",
        },
    )
    assert create.status_code == 403
    assert viewer_client.patch("/api/attendance/1", json={"work_hours": "7"}).status_code == 403
    assert viewer_client.delete("/api/attendance/1").status_code == 403


def test_admin_can_create_employee(
    client: TestClient, reference_ids: dict[str, int]
) -> None:
    response = client.post(
        "/api/employees",
        json={
            "employee_number": "FHR-0099",
            "name": "관리자등록",
            "department_id": reference_ids["qa"],
            "factory_id": reference_ids["daegu"],
            "shift_id": reference_ids["night"],
            "hired_at": "2025-02-01",
            "status": "active",
        },
    )
    assert response.status_code == 201
    assert response.json()["employee_number"] == "FHR-0099"
